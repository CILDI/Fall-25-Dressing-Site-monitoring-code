import os
import cv2
from ai import inference_helper
from uploader import upload_frame_to_supabase
from analysis import log_test_results_to_csv

def run_batch_test():
    ## USED TO TEST REAL IMAGES ##
    ## IGNORE THIS FILE ##
    # 1. Define folder path
    folder_path = "RealPictures"
    
    # 2. Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return

    print(f"--- Starting Batch Test for {folder_path} ---")

    # 3. Loop through files in the folder
    for filename in os.listdir(folder_path):
        # Process only images (JPG, PNG)
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"\nProcessing: {filename}...")
            
            file_path = os.path.join(folder_path, filename)
            
            # Read image using OpenCV
            frame = cv2.imread(file_path)
            if frame is None:
                print(f"Could not read {filename}, skipping.")
                continue

            try:
                # 4. Run AI Inference
                # Returns (result_json, annotated_image_bytes, encoded_buffer)
                result_json, _, encoded_buffer = inference_helper(frame)

                # 5. Upload to Supabase to get a URL for the CSV
                # (You can use the filename as the base name)
                image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
                public_url, photo_id = upload_frame_to_supabase(image_bytes, filename.split('.')[0])

                # 6. Log results to your CSV
                # This will use the manual columns we just added!
                log_test_results_to_csv(photo_id, public_url, result_json)
                
                print(f"Successfully logged {filename} to CSV.")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print("\n--- Batch Test Complete ---")

if __name__ == "__main__":
    run_batch_test()