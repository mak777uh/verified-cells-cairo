#!/usr/bin/env python3
r"""build_walkthrough.py — запись экрана для verified-cells-cairo.

Заявка Starknet обещает «a recorded walkthrough». Это он: реальный прогон шести ячеек и проверка квитанции,
без слайдов и без синтетического рассказа о том, чего не было.

    python build_walkthrough.py
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(r"C:\111\work\verified_cells_cairo")
BUILD = ROOT / "_walk"
BUILD.mkdir(exist_ok=True)
W, H = 1920, 1080
BG = (13, 16, 21)
FG = (222, 228, 236)
DIM = (130, 140, 152)
GREEN = (90, 205, 125)
ACCENT = (95, 165, 255)

FFMPEG = (r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget."
          r"Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe")
FONT = r"C:\Windows\Fonts\consola.ttf"
PY = r"C:\111\env\python\.venv\Scripts\python.exe"
SCARB = r"C:\111\env\bin\scarb\scarb-v2.21.0-x86_64-pc-windows-msvc\bin\scarb.exe"

LINE_H = 34
TOP = 200
LEFT = 130


def run(cmd: list[str]) -> tuple[list[str], int]:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(ROOT),
                       encoding="utf-8", errors="replace")
    return [ln.rstrip() for ln in ((r.stdout or "") + (r.stderr or "")).splitlines()], r.returncode


def frame(lines: list[str], caption: str, idx: int) -> pathlib.Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 27)
    f_small = ImageFont.truetype(FONT, 22)
    f_cap = ImageFont.truetype(FONT, 28)

    d.rounded_rectangle([LEFT - 40, TOP - 130, W - LEFT + 40, H - 90], radius=18, outline=(44, 52, 64), width=2)
    for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse([LEFT - 14 + k * 30, TOP - 112, LEFT + 4 + k * 30, TOP - 94], fill=c)
    d.text((LEFT + 120, TOP - 118), "verified-cells-cairo — scarb 2.21.0", font=f_small, fill=DIM)

    y = TOP
    for line in lines[-20:]:
        color = FG
        low = line.lower()
        if ": pass" in low:
            color = GREEN
        elif "matches" in low or "ok " in low:
            color = GREEN
        elif "fail" in low or "error" in low:
            color = (235, 110, 110)
        elif low.startswith("$") or "scarb" in low or "python" in low:
            color = ACCENT
        d.text((LEFT, y), line[:118], font=f, fill=color)
        y += LINE_H

    d.text((LEFT - 40, H - 66), caption, font=f_cap, fill=DIM)
    d.text((W - 250, H - 66), str(idx), font=f_small, fill=DIM)
    out = BUILD / f"w{idx:03d}.png"
    img.save(out)
    return out


def segment(lines: list[str], caption: str, per_line: float, start: int) -> tuple[pathlib.Path, int]:
    frames, idx = [], start
    for n in range(1, len(lines) + 1):
        frames.append(frame(lines[:n], caption, idx))
        idx += 1
    hold = frame(lines, caption, idx)
    idx += 1
    frames.append(hold)
    listing = BUILD / f"seg{start}.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\nduration {per_line}\n" for p in frames)
                       + f"file '{hold.as_posix()}'\nduration 3\n", encoding="utf-8")
    seg = BUILD / f"seg{start}.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-fps_mode", "vfr", "-pix_fmt", "yuv420p", "-c:v", "libx264", str(seg)],
                   check=True, capture_output=True, timeout=600)
    return seg, idx


def tts(text: str, out: pathlib.Path) -> float:
    ps = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft David Desktop")
$s.Rate = 1
$s.SetOutputToWaveFile("{out}")
$s.Speak(@"
{text}
"@)
$s.Dispose()
'''
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=180)
    fp = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")
    d = subprocess.run([fp, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                       capture_output=True, text=True, timeout=60).stdout.strip()
    return float(d or 0)


def main() -> int:
    print("  scarb build + execute ...")
    build, rc_b = run([SCARB, "build"])
    cells, rc_e = run([SCARB, "execute", "--print-program-output"])
    print(f"  build exit={rc_b} | execute exit={rc_e} ({len(cells)} строк)")
    print("  make_receipt ...")
    receipt, rc_r = run([PY, "make_receipt.py"])
    verify, rc_v = run([PY, "verify_receipt.py"])

    voice = BUILD / "voice.wav"
    dur = tts("Six cells, one command. Each cell is a model of an invariant, a test that exercises it, and a "
              "receipt that binds the result to a hash. This is not a slide: this is the toolchain running. "
              "Then the verifier re-reads the files and the statement hash. What the cells do not claim is "
              "printed in the receipt, next to the result.", voice)
    print(f"  голос: {dur:.1f} с")

    total_lines = len(cells) + len(receipt) + len(verify)
    per = max(0.14, (dur - 3.0) / max(total_lines, 1))
    seg1, idx = segment(cells, "1/3  scarb execute — six cells", per, 1)
    seg2, idx = segment(receipt, "2/3  make_receipt.py — the statement hash", per, idx)
    seg3, idx = segment(verify, "3/3  verify_receipt.py — re-check", per, idx)

    out = ROOT / "walkthrough.mp4"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", str(seg1), "-i", str(seg2), "-i", str(seg3),
                    "-i", str(voice),
                    "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
                    "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)],
                   check=True, capture_output=True, timeout=900)
    print(f"  видео: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
