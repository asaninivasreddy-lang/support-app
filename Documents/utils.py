import base64
from django.core.files.base import ContentFile

def base64_to_file(base64_str, file_name):
    try:
        decoded_file = base64.b64decode(base64_str)
    except Exception:
        return None

    return ContentFile(decoded_file, name=file_name)
