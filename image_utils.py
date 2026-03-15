import os
from PIL import Image
from io import BytesIO
from tempfile import NamedTemporaryFile

MAX_IMAGE_WIDTH = 300

def resize_image_for_display(image_file):
    """Resize image for display only, returns bytes."""
    if isinstance(image_file, str):
        img = Image.open(image_file)
    else:
        img = Image.open(image_file)
        image_file.seek(0)

    aspect_ratio = img.height / img.width
    new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
    img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def save_uploaded_file(uploaded_file):
    with NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(uploaded_file.getbuffer())
        return temp_file.name


def remove_file(file_path):
    try:
        os.unlink(file_path)
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")




