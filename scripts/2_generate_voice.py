"""
Step 2: Generate natural human-like voice using Microsoft Edge TTS
100% FREE - No account - No API key - Sounds very natural
Install: pip install edge-tts
"""

import json
import os
import subprocess
import asyncio
import sys


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


async def edge_tts_generate(text, output_path, voice="en-US-AriaNeural"):
    """
    Microsoft Edge TTS - free, no account, very natural human voice
    Best voices:
      en-US-AriaNeural     - Warm friendly female (best for facts)
      en-US-JennyNeural    - Clear energetic female
      en-US-GuyNeural      - Natural male voice
      en-GB-SoniaNeural    - British female
    """
    import edge_tts
    tts = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="+15%",    # Slightly faster for Shorts energy
        volume="+10%",  # Slightly louder
        pitch="+5Hz"    # Slightly higher pitch, sounds more engaging
    )
    await tts.save(output_path)
    print(f"  Voice saved: {output_path}")


def generate_segment(text, output_path):
    """Generate one audio segment using Edge TTS with espeak fallback"""
    try:
        asyncio.run(edge_tts_generate(text, output_path))
        if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            return True
    except Exception as e:
        print(f"  Edge TTS failed: {e}, using espeak fallback")

    # Fallback to espeak
    wav = output_path.replace(".mp3", ".wav")
    r = subprocess.run([
        "espeak-ng", "-v", "en-us+f3",
        "-s", "155", "-p", "58", "-a", "180",
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
        return True
    return False


def combine_audio(segment_files, output_path):
    os.makedirs("output/audio", exist_ok=True)

    # 0.4 second silence between segments (tighter for Shorts)
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

    # Get duration
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "0")
    print(f"Combined audio: {output_path} ({duration:.1f}s)")
    return duration


if __name__ == "__main__":
    data = load_video_data()
    vo = data["voiceover"]
    fruit = data["fruit"]

    os.makedirs("output/audio/segments", exist_ok=True)

    print(f"Generating voice for: {fruit}")
    print("Using Microsoft Edge TTS (natural human voice)")

    # Label each fact for display
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
    for name, text in segments:
        out = f"output/audio/segments/{name}.mp3"
        print(f"Generating: {name} — {text[:50]}...")
        generate_segment(text, out)
        segment_files.append(out)

    duration = combine_audio(segment_files, "output/audio/final_voiceover.mp3")

    if duration > 62:
        print(f"WARNING: Audio is {duration:.1f}s — over 60s limit!")
        print("Consider shortening facts in the script.")
    else:
        print(f"Audio length: {duration:.1f}s — fits in Shorts!")
