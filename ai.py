# ai.py
import cv2
import base64
import tempfile
from inference_sdk import InferenceHTTPClient

# Initialize Roboflow client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="Gl3Piz2o3nvjnAVyTJvT"
)


def inference_helper(frame):
    """
    Runs AI inference on an OpenCV frame.
    Returns:
        result_json: dict from Roboflow
        annotated_image_bytes: bytes of annotated image (if returned)
        original_image_bytes: bytes of original JPEG frame
    """
    # Encode frame to JPEG
    success, buffer = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Failed to encode frame to JPEG")

    original_image_bytes = buffer.tobytes()

    # Write temp file on disk for Roboflow
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        temp_path = tmp.name
        tmp.write(original_image_bytes)

    print("DEBUG: Temp file path:", temp_path)
    print("DEBUG: Type passed to infer():", type(temp_path))

    # Run inference using file path
    result_json = CLIENT.infer(temp_path, model_id="my-first-project-x5u0k/12")

    # Check for annotated image bytes in response (Roboflow sometimes returns 'annotated_image')
    annotated_image_bytes = None
    if "annotated_image" in result_json:
        try:
            annotated_image_bytes = base64.b64decode(result_json["annotated_image"])
        except Exception:
            annotated_image_bytes = None
    else:
        annotated_image_bytes = None

    return result_json, annotated_image_bytes, original_image_bytes
