import os
import math
import wave
import struct
from PIL import Image, ImageDraw

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)


def generate_audio_chimes():
    """Synthesize pleasant, high-quality audio chimes for activation and selection."""
    sample_rate = 44100

    # 1. Activation sound: ethereal ascending two-tone sparkle
    dur_act = 0.28
    data_act = bytearray()
    for i in range(int(sample_rate * dur_act)):
        t = float(i) / sample_rate
        env = math.exp(-10.0 * t)
        # ascending frequency sweep from 600Hz to 1100Hz
        f = 600.0 + 500.0 * (t / dur_act)
        val = 0.7 * math.sin(2.0 * math.pi * f * t) + 0.3 * math.sin(
            4.0 * math.pi * f * t
        )
        sample = int(val * env * 32767.0 * 0.45)
        sample = max(-32768, min(32767, sample))
        data_act += struct.pack("<h", sample)

    act_path = os.path.join(ASSETS_DIR, "activate.wav")
    with wave.open(act_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data_act)

    # 2. Selection sound: crisp, satisfying pop / chime
    dur_sel = 0.22
    data_sel = bytearray()
    for i in range(int(sample_rate * dur_sel)):
        t = float(i) / sample_rate
        env = math.exp(-14.0 * t)
        # A5 (880Hz) with bright E6 (1320Hz) harmonic
        val = 0.65 * math.sin(2.0 * math.pi * 880.0 * t) + 0.35 * math.sin(
            2.0 * math.pi * 1320.0 * t
        )
        sample = int(val * env * 32767.0 * 0.5)
        sample = max(-32768, min(32767, sample))
        data_sel += struct.pack("<h", sample)

    sel_path = os.path.join(ASSETS_DIR, "select.wav")
    with wave.open(sel_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data_sel)


def generate_icons():
    """Generate modern Google-style glowing circle app icon and tray icon."""
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size / 2
    radius = 96
    thickness = 24

    # Google 4-color arcs
    # Blue: -40 to 45 deg, Green: 45 to 135 deg, Yellow: 135 to 225 deg, Red: 225 to 320 deg
    colors = [
        ("#4285F4", -40, 45),  # Google Blue
        ("#34A853", 45, 135),  # Google Green
        ("#FBBC05", 135, 225),  # Google Yellow
        ("#EA4335", 225, 320),  # Google Red
    ]

    for col, start, end in colors:
        draw.arc(
            [center - radius, center - radius, center + radius, center + radius],
            start=start,
            end=end,
            fill=col,
            width=thickness,
        )

    # Central Google Lens inspired camera / magnifying glass
    lx, ly = center - 8, center - 8
    lens_r = 46
    draw.ellipse(
        [lx - lens_r, ly - lens_r, lx + lens_r, ly + lens_r],
        outline="#FFFFFF",
        width=14,
    )
    # Lens handle
    draw.line([lx + 32, ly + 32, lx + 74, ly + 74], fill="#FFFFFF", width=16)

    # Central blue dot pupil inside lens
    dot_r = 16
    draw.ellipse(
        [lx - dot_r, ly - dot_r, lx + dot_r, ly + dot_r], fill="#4285F4"
    )

    png_path = os.path.join(ASSETS_DIR, "app_icon.png")
    img.save(png_path, "PNG")

    # Generate ICO file with multiple sizes (16, 32, 48, 64, 128, 256)
    ico_path = os.path.join(ASSETS_DIR, "app_icon.ico")
    img.save(
        ico_path,
        format="ICO",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )

    # Tray icon (32x32 crisp version)
    tray_img = img.resize((32, 32), Image.Resampling.LANCZOS)
    tray_path = os.path.join(ASSETS_DIR, "tray_icon.png")
    tray_img.save(tray_path, "PNG")


if __name__ == "__main__":
    generate_audio_chimes()
    generate_icons()
    print("Assets generated successfully in:", ASSETS_DIR)
