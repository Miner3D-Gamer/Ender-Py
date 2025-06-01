from PIL import Image
import base64, zlib
import struct


def image_to_text(path: str) -> str:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    raw = img.tobytes()
    header = struct.pack(">HH", w, h)  # 2 bytes for width and height each (big-endian)
    compressed = zlib.compress(header + raw)
    return base64.b64encode(compressed).decode("ascii")


def text_to_image(text: str) -> Image.Image:
    decoded = zlib.decompress(base64.b64decode(text))
    w, h = struct.unpack(">HH", decoded[:4])
    raw = decoded[4:]
    img = Image.frombytes("RGB", (w, h), raw)
    return img
