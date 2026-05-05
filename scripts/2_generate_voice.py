"""
Step 2: Generate natural human-like voice using Microsoft Edge TTS
Using en-US-AndrewNeural with NATURAL settings (no pitch shift)
"""

import json
import os
import subprocess
import asyncio


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


async def edge_tts_generate(text, output_path, voice="en-US-AndrewNeural"):
    """
    Microsoft Edge TTS — natural human voice
    en-US-AndrewNeural — warm conversational male voice (CURRENT)
    Uses NATURAL settings — no pitch shift, mild rate boost only
    """
    import edge_tts
    tts = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate="+8%"          # Mild speed bump for energy (not too fast)
        # NO pitch shift — keeps voice natural
        # NO volume boost — keeps natural dynamics
    )
    await tts.save(output_path)
    print(f"  Voice saved: {output_path}")


def generate_segment(text, output_path):
    try:
        asyncio.run(edge_tts_generate(text, output_path))
        if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            return True
        else:
            print(f"  Edge TTS produced empty file, falling back...")
    except Exception as e:
        print(f"  Edge TTS failed: {e}")
        print(f"  Falling back to espeak...")

    # Fallback to espeak (only if Edge TTS completely fails)
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
        return True
    return False


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
    print(f"Combined audio: {output_path} ({duration:.1f}s)")
    return duration


if __name__ == "__main__":
    data = load_video_data()
    vo = data["voiceover"]
    fruit = data["fruit"]

    os.makedirs("output/audio/segments", exist_ok=True)

    print(f"Generating voice for: {fruit}")
    print(f"Voice: en-US-AndrewNeural (natural conversational male)")

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
        print(f"  Segment: {name}")
        generate_segment(text, out)
        segment_files.append(out)

    duration = combine_audio(segment_files, "output/audio/final_voiceover.mp3")

    if duration > 62:
        print(f"WARNING: Audio is {duration:.1f}s — over 60s limit!")
    else:
        print(f"Audio length: {duration:.1f}s — fits in Shorts!")
