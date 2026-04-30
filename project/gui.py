import os
import io
import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
from datetime import datetime
import time
from dotenv import load_dotenv
from ai import inference_helper
from uploader import upload_frame_to_supabase, upload_metadata_to_supabase, get_latest_metadata
from analysis import format_and_calculate_trends





def launch_gui():
    load_dotenv()
    window = tk.Tk()
    window.title("Dressing Site Feed - Supabase")


    # Camera: Channel 0 for built-in camera, 1 for USB/Bluetooth
    cap = cv2.VideoCapture(0)
    #
    # -----------------------------------------------
    # channel 0 and disable built-in camera !!!!!
    # ------------------------------------------------
    


    video_label = tk.Label(window)
    video_label.pack()


    # Shared variable to keep latest frame
    current_frame = {"frame": None}


    # Auto-Capture setup
    auto_running = False
    interval_seconds = tk.IntVar(value=10)
    countdown_label = tk.Label(window, text="")
    countdown_label.pack(pady=5)


    def update_countdown(text):
        countdown_label.config(text=text)


    def update_video_feed():
        ret, frame = cap.read()
        if ret:
            # store latest frame
            current_frame["frame"] = frame.copy()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
        video_label.after(10, update_video_feed)


    def take_snapshot():
        frame = current_frame.get("frame")
        if frame is None:
            messagebox.showerror("Error", "No camera frame available yet")
            return


        # Do network tasks in a new thread
        def worker():
            # Heartbeat logging to find the hang-point
            now = lambda: datetime.now().strftime('%H:%M:%S')
            print(f"DEBUG [{now()}] Worker: Starting metadata fetch...")
            try:
                patient_id = os.getenv("PATIENT_ID", "test_patient_001")
                last_json = get_latest_metadata(patient_id)
                
                print(f"DEBUG [{now()}] Worker: Starting AI Inference...")
                # old line
                #result_json, annotated_image_bytes, encoded_buffer = inference_helper(frame)

                # NEW ENSEMBLE LINE
                from ensemble_ai import get_unified_inference
                result_json, annotated_image_bytes, encoded_buffer = get_unified_inference(frame)

                print(f"DEBUG [{now()}] Worker: AI Complete. Printing report...")
                format_and_calculate_trends(result_json, last_json)


                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                base_name = f"snapshot_{timestamp}"


                # Upload original image bytes
                image_bytes = encoded_buffer.tobytes() if hasattr(encoded_buffer, 'tobytes') else bytes(encoded_buffer)


                public_url, photo_name = upload_frame_to_supabase(image_bytes, base_name)

                #FOR TESTING ONLY. COMMENT AFTER
                #log_test_results_to_csv(photo_name, public_url, result_json)


                # If we got an annotated_image, also upload it
                annotated_url = None
                if annotated_image_bytes:
                    annotated_public, _ = upload_frame_to_supabase(annotated_image_bytes, base_name + "_annotated")
                    annotated_url = annotated_public


                # Optionally write metadata to Supabase table
                try:
                    upload_metadata_to_supabase(public_url, photo_name, result_json, annotated_url)
                except Exception:
                    # non-fatal
                    pass

                # Show results to user
                msg = f"Uploaded: {public_url}\n"
                if annotated_url:
                    msg += f"Annotated image: {annotated_url}\n"
                detected = result_json.get("predictions") if isinstance(result_json, dict) else None
                ## Added lines begin
                #print("Predictions\n")
                #print(result_json['predictions']) #list of dictionaries

                ## Added lines end
                if detected:
                    top = []
                    for p in detected:
                        cls = p.get("class") or p.get("label") or p.get("name")
                        conf = p.get("confidence") or p.get("score")
                        
                        # NEW: Get the source we just tagged
                        src = p.get("source", "Roboflow") 
                        top.append(f"{cls} ({conf:.3f}) [via {src}]") # Add the source tag here
                    msg += "Detected: " + ", ".join(top)


                    msg += "Detected: " + ", ".join(top)
                else:
                    msg += "No detections in response."

                #messagebox.showinfo("Result", msg)
                # message box. remove comment if needed
                print(f"DEBUG [{now()}] Worker: All tasks complete.")

            except Exception as e:
                #print(f"ERROR [{now()}] Worker crashed: {e}")
                # Thread-safe way to show error in Tkinter
                #window.after(0, lambda: messagebox.showerror("Error", str(e)))
                #messagebox.showerror("Error", str(e)) COMMENTED
                error_msg = str(e) # Convert the error to a string immediately
                print(f"ERROR: {error_msg}")
                
                # We pass error_msg as a default argument to the lambda to "freeze" its value
                window.after(0, lambda err=error_msg: messagebox.showerror("Error", err))


        threading.Thread(target=worker, daemon=True).start()

    def auto_capture_loop():
        nonlocal auto_running
        while auto_running:
            for i in range(interval_seconds.get(), 0, -1):
                if not auto_running:
                    update_countdown("Auto-Capture stopped")
                    return
                update_countdown(f"Next snapshot in: {i}s")
                time.sleep(1)
            take_snapshot()

    def start_auto_capture():
        nonlocal auto_running
        if not auto_running:
            auto_running = True
            threading.Thread(target=auto_capture_loop, daemon=True).start()

    def stop_auto_capture():
        nonlocal auto_running
        auto_running = False
        update_countdown("Auto-Capture stopped")

    tk.Button(window, text="Capture & Upload", command=take_snapshot).pack(pady=10)

    auto_frame = tk.Frame(window)
    auto_frame.pack(pady=10)
    tk.Label(auto_frame, text="Auto-capture interval (sec):").pack(side="left")
    tk.Entry(auto_frame, textvariable=interval_seconds, width=5).pack(side="left", padx=5)
    tk.Button(auto_frame, text="Start Auto-Capture", command=start_auto_capture).pack(side="left", padx=5)
    tk.Button(auto_frame, text="Stop Auto-Capture", command=stop_auto_capture).pack(side="left")

    update_video_feed()

    try:
        window.mainloop()
    finally:
        # This force-stops everything when the window closes
        auto_running = False 
        cap.release()
        cv2.destroyAllWindows()
        print("\nDEBUG: Application closed and hardware released.")
        # This forces the entire Python process (including stuck threads) to die immediately
        os._exit(0)
    
