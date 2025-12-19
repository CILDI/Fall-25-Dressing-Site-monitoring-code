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
from uploader import upload_frame_to_supabase, upload_metadata_to_supabase




def launch_gui():
    load_dotenv()
    window = tk.Tk()
    window.title("Dressing Site Feed - Supabase")


    # Camera: Channel 0 for built-in camera, 1 for USB/Bluetooth
    cap = cv2.VideoCapture(0)


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
            try:
                # Run AI inference (returns JSON, annotated_image_bytes, and encoded buffer)
                result_json, annotated_image_bytes, encoded_buffer = inference_helper(frame)


                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                base_name = f"snapshot_{timestamp}"


                # Upload original image bytes
                image_bytes = encoded_buffer.tobytes() if hasattr(encoded_buffer, 'tobytes') else bytes(encoded_buffer)


                public_url, photo_name = upload_frame_to_supabase(image_bytes, base_name)


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
                if detected:
                    top = []
                    for p in detected:
                        cls = p.get("class") or p.get("label") or p.get("name")
                        conf = p.get("confidence") or p.get("score")
                        top.append(f"{cls} ({conf})")
                    msg += "Detected: " + ", ".join(top)
                else:
                    msg += "No detections in response."

                messagebox.showinfo("Result", msg)

            except Exception as e:
                messagebox.showerror("Error", str(e))

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
    window.mainloop()

    # cleanup
    cap.release()
    cv2.destroyAllWindows()