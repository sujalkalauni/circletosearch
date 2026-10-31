import io
import asyncio
import threading
from PIL import Image

try:
    import winsdk.windows.media.ocr as win_ocr
    import winsdk.windows.graphics.imaging as imaging
    import winsdk.windows.storage.streams as streams

    WINSDK_AVAILABLE = True
except ImportError:
    WINSDK_AVAILABLE = False


def pil_image_to_software_bitmap(image: Image.Image):
    """Convert a PIL Image to Windows SoftwareBitmap for Windows OCR Engine."""
    # Convert image to RGB BMP in memory
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="BMP")
    data = bytearray(buf.getvalue())

    async def _convert():
        stream = streams.InMemoryRandomAccessStream()
        writer = streams.DataWriter(stream)
        writer.write_bytes(data)
        await writer.store_async()
        await writer.flush_async()
        writer.detach_stream()
        stream.seek(0)
        decoder = await imaging.BitmapDecoder.create_async(stream)
        return await decoder.get_software_bitmap_async()

    return asyncio.run(_convert())


def extract_text_from_image(image: Image.Image) -> str:
    """Synchronously extract text from an image using Windows 10/11 native OCR."""
    if not WINSDK_AVAILABLE:
        return ""

    try:
        software_bitmap = pil_image_to_software_bitmap(image)

        async def _recognize():
            engine = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                return ""
            result = await engine.recognize_async(software_bitmap)
            return result.text.strip() if result else ""

        return asyncio.run(_recognize())
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def extract_text_async(image: Image.Image, on_complete):
    """Run OCR in a background thread and invoke on_complete(text)."""

    def _worker():
        text = extract_text_from_image(image)
        if on_complete:
            on_complete(text)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
