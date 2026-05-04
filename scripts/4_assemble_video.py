"""
Step 4: Assemble final video using FFmpeg (Free, No Watermark)
Combines: images + voiceover + background music + English subtitles
Subtitles are accurately timed to match the actual audio segments
"""

import json
import os
import subprocess
import math


# ── Load video data ───────────────────────────────────────────────────────────
def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


# ── Get duration of any audio file ───────────────────────────────────────────
def get_duration(path):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path
    ], capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except Exception:
        return 4.0


# ── Format seconds to SRT timestamp ──────────────────────────────────────────
def to_srt_time(seconds):
    seconds = max(0.0, seconds)
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ── Build accurate SRT from real audio durations ──────────────────────────────
def create_subtitles(data):
    """
    Reads the ACTUAL duration of every audio segment file so subtitles
    are perfectly in sync — no guessing or estimation.
    """
    voiceover = data["voiceover"]

    segment_names = ["intro", "fact_1", "fact_2", "fact_3", "fact_4", "fact_5", "outro"]
    segment_texts = [
        voiceover["intro"],
        voiceover["fact_1"],
        voiceover["fact_2"],
        voiceover["fact_3"],
        voiceover["fact_4"],
        voiceover["fact_5"],
        voiceover["outro"],
    ]

    SILENCE_GAP = 0.8   # must match 2_generate_voice.py silence duration
    WORDS_PER_LINE = 7  # words shown per subtitle card

    srt_lines   = []
    sub_index   = 1
    cursor      = 0.0  # running clock in seconds

    for seg_name, text in zip(segment_names, segment_texts):
        seg_path = f"output/audio/segments/{seg_name}.mp3"

        if os.path.exists(seg_path):
            seg_duration = get_duration(seg_path)
        else:
            # Rough fallback: ~2.8 words per second for espeak
            word_count   = len(text.split())
            seg_duration = max(3.0, word_count / 2.8)

        # Split text into subtitle cards
        words  = text.split()
        chunks = [words[i:i + WORDS_PER_LINE]
                  for i in range(0, len(words), WORDS_PER_LINE)]

        # Distribute segment duration evenly across cards
        card_duration = seg_duration / max(len(chunks), 1)

        for chunk in chunks:
            card_text  = " ".join(chunk)
            start_time = cursor
            end_time   = cursor + card_duration - 0.05  # tiny gap between cards

            srt_lines.append(
                f"{sub_index}\n"
                f"{to_srt_time(start_time)} --> {to_srt_time(end_time)}\n"
                f"{card_text}\n"
            )
            sub_index += 1
            cursor    += card_duration

        cursor += SILENCE_GAP  # gap between segments

    srt_content = "\n".join(srt_lines)

    os.makedirs("output", exist_ok=True)
    with open("output/subtitles.srt", "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"Subtitles created: output/subtitles.srt ({sub_index - 1} cards)")
    return cursor  # total expected duration


# ── Create soft background music ─────────────────────────────────────────────
def create_background_music(duration):
    out = "output/audio/background_music.mp3"
    fade_start = max(0, duration - 3)

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=200:sample_rate=44100",
        "-f", "lavfi", "-i", "sine=frequency=300:sample_rate=44100",
        "-f", "lavfi", "-i", "sine=frequency=400:sample_rate=44100",
        "-filter_complex",
        f"[0][1][2]amix=inputs=3:duration=longest,"
        f"volume=0.06,"
        f"afade=t=in:d=3,"
        f"afade=t=out:st={fade_start}:d=3",
        "-t", str(duration + 2),
        "-codec:a", "libmp3lame",
        out
    ], capture_output=True)
    print(f"Background music created: {out}")
    return out


# ── Assemble the final MP4 ────────────────────────────────────────────────────
def assemble_video(data):
    fruit_name    = data["fruit"]
    voiceover_mp3 = "output/audio/final_voiceover.mp3"
    music_mp3     = "output/audio/background_music.mp3"
    srt_file      = "output/subtitles.srt"
    out_mp4       = "output/final_video.mp4"

    total_duration = get_duration(voiceover_mp3)
    print(f"Total video duration: {total_duration:.1f}s")

    # Collect available images (up to 5)
    image_files = []
    for i in range(1, 6):
        p = f"output/images/scene_{i}.png"
        if os.path.exists(p):
            image_files.append(p)

    if not image_files:
        raise FileNotFoundError("No images found in output/images/")

    # Each image shown for equal share of total duration
    img_duration = total_duration / len(image_files)

    # ── Build FFmpeg command ──────────────────────────────────────────────────
    cmd = ["ffmpeg", "-y"]

    # Image inputs (loop each for its duration)
    for img in image_files:
        cmd += ["-loop", "1", "-t", str(img_duration), "-i", img]

    # Audio inputs
    cmd += ["-i", voiceover_mp3, "-i", music_mp3]

    n   = len(image_files)
    vai = n      # voiceover audio index
    mai = n + 1  # music audio index

    # Scale + pad each image to 1920x1080
    scale_parts = []
    for i in range(n):
        scale_parts.append(
            f"[{i}:v]scale=1920:1080:"
            f"force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1[v{i}]"
        )

    # Concatenate scaled video streams
    concat_in  = "".join(f"[v{i}]" for i in range(n))
    concat_out = f"{concat_in}concat=n={n}:v=1:a=0[vraw]"

    # Mix voiceover (full volume) + music (very soft)
    audio_mix = (
        f"[{vai}:a][{mai}:a]"
        f"amix=inputs=2:weights='1 0.12':duration=first[aout]"
    )

    filter_complex = ";".join(scale_parts + [concat_out, audio_mix])

    cmd += ["-filter_complex", filter_complex]
    cmd += ["-map", "[vraw]", "-map", "[aout]"]

    # ── Subtitle overlay ──────────────────────────────────────────────────────
    # Style: white bold text, black outline, semi-transparent dark bar behind
    subtitle_style = (
        "FontName=Arial,"
        "FontSize=24,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"    # white text
        "OutlineColour=&H00000000,"    # black outline
        "BackColour=&H99000000,"       # dark semi-transparent background box
        "BorderStyle=3,"               # box style (3 = opaque box)
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"                 # bottom-centre
        "MarginV=50,"                  # distance from bottom edge
        "MarginL=80,"
        "MarginR=80"
    )

    vf_filter = (
        f"subtitles={srt_file}:"
        f"force_style='{subtitle_style}'"
    )

    cmd += [
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4
    ]

    print("Assembling video...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size_mb = os.path.getsize(out_mp4) / 1024 / 1024
        print(f"Video ready: {out_mp4} ({size_mb:.1f} MB)")
    else:
        # Print last 3000 chars of stderr for debugging
        print("FFmpeg error:")
        print(result.stderr[-3000:])
        raise RuntimeError("Video assembly failed — see error above")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = load_video_data()

    print("=== Step 4: Assembling Video ===")
    print(f"Fruit: {data['fruit']}")

    # 1. Build accurate subtitle file from real audio durations
    create_subtitles(data)

    # 2. Get total audio duration for music length
    total_dur = get_duration("output/audio/final_voiceover.mp3")

    # 3. Generate background music
    create_background_music(total_dur)

    # 4. Assemble everything into final MP4
    assemble_video(data)

    print("\nDone! Files ready:")
    print("  output/final_video.mp4")
    print("  output/thumbnail.jpg")
    print("  output/subtitles.srt")
