# uploader_supabase.py
import os
import io
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "uploads")
TEST_PATIENT = os.getenv("PATIENT_ID", "test_patient_001")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def _safe_upload_bytes(bucket: str, path: str, data: bytes):
    # The supabase client returns different shapes depending on versions. Try/catch for safety.
    try:
        res = supabase.storage.from_(bucket).upload(path, data, {"content-type": "image/jpeg"})
        # Newer clients return a dict-like object with 'error'
        if isinstance(res, dict) and res.get("error"):
            raise Exception(res.get("error"))
        # some versions may return an object with 'error' attr
        if hasattr(res, "error") and res.error:
            raise Exception(res.error)
        # Build and return public URL manually
        SUPABASE_URL = "https://xvhnrqpcgitxvumllxiu.supabase.co"
        photo_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
        print("Uploaded to Supabase:", photo_url)
        return photo_url
    except Exception as exc:
        raise




def upload_frame_to_supabase(image_bytes: bytes, photo_name: str):
    """ Upload image_bytes (bytes) to Supabase Storage, return public URL and photo_name """
    file_path = f"{TEST_PATIENT}/{photo_name}.jpg"

    photo_url = _safe_upload_bytes(SUPABASE_BUCKET, file_path, image_bytes)

    # get_public_url also varies by client; handle both shapes
    try:
        url_obj = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        if isinstance(url_obj, dict):
            public_url = url_obj.get("publicURL") or url_obj.get("public_url")
        else:
            # object with attribute
            public_url = getattr(url_obj, "publicURL", None) or getattr(url_obj, "public_url", None)
    except Exception:
        # Last resort: construct URL (works for default supabase storage path)
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"

    print("Uploaded to Supabase:", public_url)
    return photo_url, photo_name




def upload_metadata_to_supabase(photo_url, photo_name, result_json=None, annotated_url=None):
    """ (Optional) Insert metadata into a Supabase table called 'photos' if you created one. """
    timestamp = datetime.utcnow().isoformat()
    status = "processed" if result_json else "pending"
    data = {
    "patient": TEST_PATIENT,
    "photo_name": photo_name,
    "image_url": photo_url,
    "result_json": result_json,
    "annotated_url": annotated_url,
    "status": status,
    "created_at": timestamp,
    }
    try:
        res = supabase.table("photos").insert(data).execute()
        # older clients: res.error
        if hasattr(res, "error") and res.error:
            print("Supabase insert error:", res.error)
        else:
            print(f"Metadata for '{photo_name}' inserted into Supabase table 'photos'.")
    except Exception as e:
        print("Skipping metadata insert (table may not exist):", e)
