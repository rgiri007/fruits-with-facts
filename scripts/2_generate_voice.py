"""
Step 2: Generate natural human-like voice using Microsoft Edge TTS
With multiple fallback strategies to avoid silent espeak fallback
"""

import json
import os
import subprocess
import asyncio
import sys


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


# ── Method 1: Edge TTS via CLI command (most reliable) ───────────────────────
def edge_tts_cli(text, output_path, voice="en-US-AndrewNeural"):
    """
    Use edge-tts command-line interface — more reliable than Python API.
    Returns True only if MP3 was actually created with reasonable size.
    """
    try:
        # Write text to temp file (avoids shell escaping issues)
        text_file = output_path.replace(".mp3", ".txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)

        result = subprocess.run([
            "edge-tts",
            "--voice", voice,
            "--file", text_file,
            "--write-media", output_path
        ], capture_output=True, text=True, timeout=60)

        # Clean up text file
        if os.path.exists(text_file):
            os.remove(text_file)

        if result.returncode == 0 and os.path.exists(output_path) \
           and os.path.getsize(output_path) > 1000:
            return True
        else:
            print(f"  CLI failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("  CLI timeout (60s)")
        return False
    except FileNotFoundError:
        print("  edge-tts CLI not installed")
        return False
    except Exception as e:
        print(f"  CLI error: {e}")
        return False


# ── Method 2: Edge TTS Python API ────────────────────────────────────────────
async def edge_tts_python(text, output_path, voice="en-US-AndrewNeural"):
    try:
        import edge_tts
        tts = edge_tts.Communicate(text=text, voice=voice)
        await tts.save(output_path)
        return True
    except Exception as e:
        print(f"  Python API error: {e}")
        return False


def edge_tts_python_sync(text, output_path):
    try:
        success = asyncio.run(edge_tts_python(text, output_path))
        if success and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
        return False
    except Exception as e:
        print(f"  Python sync error: {e}")
        return False


# ── Method 3: Try with different voice if Andrew fails ───────────────────────
BACKUP_VOICES = [
    "en-US-AndrewNeural",
    "en-US-BrianNeural",
    "en-US-GuyNeural",
    "en-US-DavisNeural",
    "en-GB-RyanNeural",
]


def generate_segment(text, output_path):
    """
    Try multiple methods in order. Only fall back to espeak if EVERYTHING fails.
    """
    print(f"  Trying Edge TTS (CLI method)...")

    # Method 1: CLI with primary voice
    if edge_tts_cli(text, output_path, "en-US-AndrewNeural"):
        print(f"  SUCCESS (CLI Andrew): {output_path}")
        return "edge_tts"

    # Method 2: CLI with backup voices
    for voice in BACKUP_VOICES[1:]:
        print(f"  Trying CLI with {voice}...")
        if edge_tts_cli(text, output_path, voice):
            print(f"  SUCCESS (CLI {voice}): {output_path}")
            return "edge_tts"

    # Method 3: Python API
    print(f"  Trying Edge TTS Python API...")
    if edge_tts_python_sync(text, output_path):
        print(f"  SUCCESS (Python API): {output_path}")
        return "edge_tts"

    # ALL Edge TTS methods failed — use espeak as LAST resort with WARNING
    print(f"  WARNING: All Edge TTS methods failed!")
    print(f"  Using espeak fallback (will sound robotic)")

    wav = output_path.replace(".mp3", ".wav")
    r = subprocess.run([
        "espeak-ng", "-v", "en-us+m3",
        "-s", "155", "-p", "55", "-a", "180",
        "-w", wav, text
    ], capture_output=True)

    if r.returncode == 0:
        subprocess.run([
            "ffmpeg", "-y", "-i", wav,
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            output_path
        ], capture_output=True)
        if os.path.exists(wav):
            os.remove(wav)
        return "espeak"

    return "failed"


def combine_audio(segment_files, output_path):
    os.makedirs("output/audio", exist_ok=True)

    silence = "output/audio/silence.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", "0.4", "-codec:a", "libmp3lame", silence
    ], capture_output=True)

    list_file = "output/audio/concat_list.txt"
    with open(list_file, "w") as f:
        for i, seg in enumerate(segment_files):
            abs_seg = os.path.abspath(seg)
            abs_sil = os.path.abspath(silence)
            f.write(f"file '{abs_seg}'\n")
            if i < len(segment_files) - 1:
                f.write(f"file '{abs_sil}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-codec:a", "libmp3lame", "-qscale:a", "2",
        output_path
    ], capture_output=True)

    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", output_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "0")
    print(f"\nCombined audio: {output_path} ({duration:.1f}s)")
    return duration


if __name__ == "__main__":
    data = load_video_data()
    vo = data["voiceover"]
    fruit = data["fruit"]

    os.makedirs("output/audio/segments", exist_ok=True)

    print(f"=== Generating voice for: {fruit} ===")
    print(f"Primary voice: en-US-AndrewNeural\n")

    segments = [
        ("hook",   vo["hook"]),
        ("fact_1", f"Fact 1! {vo['fact_1']}"),
        ("fact_2", f"Fact 2! {vo['fact_2']}"),
        ("fact_3", f"Fact 3! {vo['fact_3']}"),
        ("fact_4", f"Fact 4! {vo['fact_4']}"),
        ("fact_5", f"Fact 5! {vo['fact_5']}"),
        ("outro",  vo["outro"]),
    ]

    segment_files = []
    methods_used = []
    for name, text in segments:
        out = f"output/audio/segments/{name}.mp3"
        print(f"\nSegment: {name}")
        method = generate_segment(text, out)
        methods_used.append(method)
        segment_files.append(out)

    duration = combine_audio(segment_files, "output/audio/final_voiceover.mp3")

    # Summary report
    print("\n=== Voice Generation Report ===")
    edge_count = methods_used.count("edge_tts")
    espeak_count = methods_used.count("espeak")
    failed_count = methods_used.count("failed")

    print(f"Edge TTS (natural):  {edge_count}/{len(segments)} segments")
    print(f"espeak (robotic):    {espeak_count}/{len(segments)} segments")
    print(f"Failed:              {failed_count}/{len(segments)} segments")

    if espeak_count > 0:
        print("\n!!! WARNING !!!")
        print("Some segments used robotic espeak fallback!")
        print("This means Edge TTS service is having issues.")
        print("Check the logs above for the actual error.")
        # Don't fail the build — the audio still plays
    elif edge_count == len(segments):
        print("\nAll segments used natural Edge TTS!")
