"""
Step 4: Assemble final video using FFmpeg (Free, No Watermark)
Combines: images + voiceover + background music + English subtitles
Fixed: all filters merged into one filter_complex — no conflict
"""

import json
import os
import subprocess


# ── Load video data ───────────────────────────────────────────────────────────
def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


# ── Get duration of any audio/video file ─────────────────────────────────────
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


# ── Format seconds → SRT timestamp ───────────────────────────────────────────
def to_srt_time(seconds):
    seconds = max(0.0, seconds)
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ── Build accurate SRT subtitles ──────────────────────────────────────────────
def create_subtitles(data):
    voiceover = data["voiceover"]
    seg_names = ["intro","fact_1","fact_2","fact_3","fact_4","fact_5","outro"]
    seg_texts = [voiceover[k] for k in seg_names]

    SILENCE_GAP    = 0.8
    WORDS_PER_LINE = 7

    srt_lines = []
    idx       = 1
    cursor    = 0.0

    for name, text in zip(seg_names, seg_texts):
        seg_path = f"output/audio/segments/{name}.mp3"
        seg_dur  = get_duration(seg_path) if os.path.exists(seg_path) \
                   else max(3.0, len(text.split()) / 2.8)

        words  = text.split()
        chunks = [words[i:i+WORDS_PER_LINE]
                  for i in range(0, len(words), WORDS_PER_LINE)]
        card_dur = seg_dur / max(len(chunks), 1)

        for chunk in chunks:
            start = cursor
            end   = cursor + card_dur - 0.05
            srt_lines.append(
                f"{idx}\n{to_srt_time(start)} --> {to_srt_time(end)}\n"
                f"{' '.join(chunk)}\n"
            )
            idx    += 1
            cursor += card_dur

        cursor += SILENCE_GAP

    os.makedirs("output", exist_ok=True)
    srt_path = os.path.abspath("output/subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    print(f"Subtitles: {srt_path} ({idx-1} cards)")
    return srt_path


# ── Generate soft background music ───────────────────────────────────────────
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
        f"volume=0.06,afade=t=in:d=3,afade=t=out:st={fade_start}:d=3",
        "-t", str(duration + 2),
        "-codec:a", "libmp3lame", out
    ], capture_output=True)
    print(f"Background music: {out}")
    return out


# ── Assemble final MP4 ────────────────────────────────────────────────────────
def assemble_video(data, srt_path):
    voiceover_mp3 = "output/audio/final_voiceover.mp3"
    music_mp3     = "output/audio/background_music.mp3"
    out_mp4       = "output/final_video.mp4"

    total_dur = get_duration(voiceover_mp3)
    print(f"Total duration: {total_dur:.1f}s")

    # Collect images
    image_files = [f"output/images/scene_{i}.png" for i in range(1, 6)
                   if os.path.exists(f"output/images/scene_{i}.png")]
    if not image_files:
        raise FileNotFoundError("No images found in output/images/")

    img_dur = total_dur / len(image_files)
    n       = len(image_files)

    # ── Build FFmpeg command ──────────────────────────────────────────────────
    cmd = ["ffmpeg", "-y"]

    # Image inputs
    for img in image_files:
        cmd += ["-loop", "1", "-t", str(img_dur), "-i", img]

    # Audio inputs  (index n = voiceover, n+1 = music)
    cmd += ["-i", voiceover_mp3, "-i", music_mp3]

    # ── Single filter_complex with EVERYTHING inside ──────────────────────────
    # 1. Scale every image to 1920x1080
    scale_parts = []
    for i in range(n):
        scale_parts.append(
            f"[{i}:v]scale=1920:1080:"
            f"force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1[sv{i}]"
        )

    # 2. Concat scaled streams → [vconcat]
    concat_in  = "".join(f"[sv{i}]" for i in range(n))
    concat_out = f"{concat_in}concat=n={n}:v=1:a=0[vconcat]"

    # 3. Burn subtitles into [vconcat] → [vout]
    #    Use absolute path and escape colons for FFmpeg filter syntax
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    subtitle_style = (
        "FontName=Arial,FontSize=24,Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BackColour=&H99000000,"
        "BorderStyle=3,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=50,MarginL=60,MarginR=60"
    )
    sub_filter = (
        f"[vconcat]subtitles='{srt_escaped}':"
        f"force_style='{subtitle_style}'[vout]"
    )

    # 4. Mix voiceover + background music → [aout]
    audio_mix = (
        f"[{n}:a][{n+1}:a]"
        f"amix=inputs=2:weights='1 0.12':duration=first[aout]"
    )

    # Combine all filter parts
    filter_complex = ";".join(scale_parts + [concat_out, sub_filter, audio_mix])

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",   # video with subtitles burned in
        "-map", "[aout]",   # mixed audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4
    ]

    print("Assembling video (this takes 1-2 minutes)...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size_mb = os.path.getsize(out_mp4) / 1024 / 1024
        print(f"Video ready: {out_mp4} ({size_mb:.1f} MB)")
    else:
        print("FFmpeg error output:")
        print(result.stderr[-3000:])
        raise RuntimeError("Video assembly failed")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = load_video_data()
    print(f"=== Assembling video for: {data['fruit']} ===")

    # 1. Accurate subtitles from real audio durations
    srt_path = create_subtitles(data)

    # 2. Background music matching voiceover length
    total_dur = get_duration("output/audio/final_voiceover.mp3")
    create_background_music(total_dur)

    # 3. Assemble everything — one filter_complex, no conflicts
    assemble_video(data, srt_path)

    print("\nAll done!")
    print("  output/final_video.mp4  — ready to upload")
    print("  output/thumbnail.jpg    — ready to upload")
    print("  output/subtitles.srt    — subtitle file")
