import os
import winsound
import threading

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ACTIVATE_WAV = os.path.join(ASSETS_DIR, "activate.wav")
SELECT_WAV = os.path.join(ASSETS_DIR, "select.wav")


def play_sound_async(wav_file: str):
    """Play a WAV sound asynchronously using Windows native winsound."""
    if not os.path.exists(wav_file):
        return

    def _play():
        try:
            winsound.PlaySound(
                wav_file,
                winsound.SND_FILENAME
                | winsound.SND_ASYNC
                | winsound.SND_NODEFAULT,
            )
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def play_activate_sound(enabled: bool = True):
    if enabled:
        play_sound_async(ACTIVATE_WAV)


def play_select_sound(enabled: bool = True):
    if enabled:
        play_sound_async(SELECT_WAV)
