import io
import urllib.parse
import webbrowser
import threading
import requests
from PIL import Image

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def upload_to_google_lens(image: Image.Image, timeout: int = 10) -> str:
    """Upload cropped image to Google Lens v3 upload endpoint.

    Returns the Google Lens visual search results URL.
    """
    buf = io.BytesIO()
    # Save as high-quality JPEG
    image.convert("RGB").save(buf, format="JPEG", quality=92)
    buf.seek(0)

    headers = {"User-Agent": USER_AGENT}
    files = {"encoded_image": ("search_image.jpg", buf, "image/jpeg")}

    try:
        res = requests.post(
            "https://lens.google.com/v3/upload",
            files=files,
            headers=headers,
            allow_redirects=False,
            timeout=timeout,
        )

        # Google returns 303 See Other with Location header pointing to search results
        if res.status_code in (302, 303, 307) and "Location" in res.headers:
            return res.headers["Location"]
        elif res.status_code == 200:
            return res.url
        else:
            print(f"Lens upload returned status {res.status_code}")
            return "https://lens.google.com/"
    except Exception as e:
        print(f"Error uploading to Google Lens: {e}")
        return "https://lens.google.com/"


def open_google_lens_async(image: Image.Image, on_url_ready=None):
    """Upload to Google Lens in a background thread and immediately open in default browser."""

    def _worker():
        url = upload_to_google_lens(image)
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Error opening browser: {e}")
        if on_url_ready:
            on_url_ready(url)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def search_google_text(text: str):
    """Open Google Web Search for the recognized text."""
    if not text.strip():
        return
    query = urllib.parse.quote_plus(text.strip())
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)


def translate_google_text(text: str):
    """Open Google Translate with the recognized text."""
    if not text.strip():
        return
    query = urllib.parse.quote_plus(text.strip())
    url = f"https://translate.google.com/?sl=auto&tl=en&text={query}&op=translate"
    webbrowser.open(url)
