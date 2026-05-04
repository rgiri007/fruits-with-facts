“””
Step 4: Assemble final video using FFmpeg (Free, No Watermark)
Combines: images + voiceover + background music + captions
“””

import json
import os
import subprocess
import math

# ── Load video data ───────────────────────────────────────────────────────────

def load_video_data():
with open(“output/video_data.json”, “r”) as f:
return json.load(f)

# ── Get audio duration ────────────────────────────────────────────────────────

def get_audio_duration(audio_path):
result = subprocess.run([
“ffprobe”, “-v”, “error”,
“-show_entries”, “format=duration”,
“-of”, “default=noprint_wrappers=1:nokey=1”,
audio_path
], capture_output=True, text=True)

```
try:
    return float(result.stdout.strip())
except Exception:
    return 30.0  # default fallback
```

# ── Get segment durations ─────────────────────────────────────────────────────

def get_segment_durations():
segments = [“intro”, “fact_1”, “fact_2”, “fact_3”, “fact_4”, “fact_5”, “outro”]
durations = []
for seg in segments:
path = f”output/audio/segments/{seg}.mp3”
if os.path.exists(path):
durations.append(get_audio_duration(path))
else:
durations.append(4.0)
return durations

# ── Create subtitle/caption file (SRT) ───────────────────────────────────────

def create_subtitles(data, segment_durations):
voiceover = data[“voiceover”]
segments = [
voiceover[“intro”],
voiceover[“fact_1”],
voiceover[“fact_2”],
voiceover[“fact_3”],
voiceover[“fact_4”],
voiceover[“fact_5”],
voiceover[“outro”],
]

```
srt_content = ""
current_time = 0.0
subtitle_index = 1
silence_gap = 0.7

for i, (text, duration) in enumerate(zip(segments, segment_durations)):
    # Split text into smaller chunks for readability
    words = text.split()
    chunk_size = 8  # words per subtitle line
    chunks = [words[j:j+chunk_size] for j in range(0, len(words), chunk_size)]
    chunk_duration = duration / len(chunks)

    for chunk in chunks:
        chunk_text = " ".join(chunk)
        start = current_time
        end = current_time + chunk_duration

        start_str = format_srt_time(start)
        end_str = format_srt_time(end)

        srt_content += f"{subtitle_index}\n{start_str} --> {end_str}\n{chunk_text}\n\n"
        subtitle_index += 1
        current_time += chunk_duration

    current_time += silence_gap  # silence gap between segments

os.makedirs("output", exist_ok=True)
with open("output/subtitles.srt", "w", encoding="utf-8") as f:
    f.write(srt_content)

print("✅ Subtitles created: output/subtitles.srt")
```

def format_srt_time(seconds):
h = int(seconds // 3600)
m = int((seconds % 3600) // 60)
s = int(seconds % 60)
ms = int((seconds % 1) * 1000)
return f”{h:02d}:{m:02d}:{s:02d},{ms:03d}”

# ── Create background music (sine wave tone, royalty-free) ───────────────────

def create_background_music(duration, output_path):
“”“Generate soft ambient background using FFmpeg audio filters - no copyright”””
subprocess.run([
“ffmpeg”, “-y”,
“-f”, “lavfi”,
# Gentle ambient tone: two sine waves mixed together
“-i”, “sine=frequency=220:sample_rate=44100”,
“-f”, “lavfi”,
“-i”, “sine=frequency=330:sample_rate=44100”,
“-filter_complex”,
“[0][1]amix=inputs=2:duration=longest,volume=0.08,afade=t=in:d=3,afade=t=out:st={fade_start}:d=3”.format(
fade_start=max(0, duration - 3)
),
“-t”, str(duration),
“-codec:a”, “libmp3lame”,
output_path
], capture_output=True)
print(f”✅ Background music generated: {output_path}”)

# ── Assemble final video ──────────────────────────────────────────────────────

def assemble_video(data, total_duration):
fruit_name = data[“fruit”]
image_files = [f”output/images/scene_{i}.png” for i in range(1, 6)]

```
# Each image shows for roughly equal time
image_duration = total_duration / len(image_files)

# Build FFmpeg input list
inputs = []
for img in image_files:
    if os.path.exists(img):
        inputs.extend(["-loop", "1", "-t", str(image_duration), "-i", img])
    else:
        # Use first image as fallback
        inputs.extend(["-loop", "1", "-t", str(image_duration), "-i", image_files[0]])

# Build filter complex for crossfade transitions between images
filter_parts = []
for i in range(len(image_files)):
    filter_parts.append(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")

# Concat all video streams
concat_inputs = "".join([f"[v{i}]" for i in range(len(image_files))])
filter_parts.append(f"{concat_inputs}concat=n={len(image_files)}:v=1:a=0[vout]")

filter_complex = ";".join(filter_parts)

# Add subtitle styling
subtitle_filter = (
    "subtitles=output/subtitles.srt:force_style='"
    "FontName=Arial,"
    "FontSize=22,"
    "PrimaryColour=&H00FFFFFF,"   # White text
    "OutlineColour=&H00000000,"   # Black outline
    "BackColour=&H80000000,"      # Semi-transparent background
    "Bold=1,"
    "Outline=2,"
    "Shadow=1,"
    "Alignment=2,"                # Bottom center
    "MarginV=40"
    "'"
)

# Final assembly command
cmd = [
    "ffmpeg", "-y",
    *inputs,
    "-i", "output/audio/final_voiceover.mp3",
    "-i", "output/audio/background_music.mp3",
    "-filter_complex", filter_complex,
    "-map", "[vout]",
    # Mix voiceover (loud) + music (soft)
    "-filter_complex", f"[{len(image_files)}:a][{len(image_files)+1}:a]amix=inputs=2:weights='1 0.15'[aout]",
    "-map", "[aout]",
    "-vf", subtitle_filter,
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    "-t", str(total_duration),
    "output/final_video.mp4"
]

# Simplified command (more reliable)
simple_cmd = [
    "ffmpeg", "-y",
]

# Add image inputs
for img in image_files:
    if os.path.exists(img):
        simple_cmd.extend(["-loop", "1", "-t", str(image_duration), "-i", img])

simple_cmd.extend([
    "-i", "output/audio/final_voiceover.mp3",
    "-i", "output/audio/background_music.mp3",
    "-filter_complex",
    f"[0:v][1:v][2:v][3:v][4:v]concat=n=5:v=1:a=0[video];"
    f"[{len(image_files)}:a][{len(image_files)+1}:a]amix=inputs=2:weights='1 0.15'[audio]",
    "-map", "[video]",
    "-map", "[audio]",
    "-vf", (
        "scale=1920:1080:force_original_aspect_ratio=decrease,"
        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
        f"subtitles=output/subtitles.srt:force_style='"
        "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BackColour=&H80000000,"
        "Bold=1,Outline=2,Shadow=1,Alignment=2,MarginV=40'"
    ),
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    "-shortest",
    "output/final_video.mp4"
])

print("🎬 Assembling video with FFmpeg...")
result = subprocess.run(simple_cmd, capture_output=True, text=True)

if result.returncode == 0:
    size_mb = os.path.getsize("output/final_video.mp4") / 1024 / 1024
    print(f"✅ Video assembled: output/final_video.mp4 ({size_mb:.1f} MB)")
else:
    print(f"❌ FFmpeg error:\n{result.stderr[-2000:]}")
    raise Exception("Video assembly failed")
```

# ── Main ──────────────────────────────────────────────────────────────────────

if **name** == “**main**”:
data = load_video_data()

```
# Get audio duration
audio_path = "output/audio/final_voiceover.mp3"
total_duration = get_audio_duration(audio_path)
print(f"⏱️ Total video duration: {total_duration:.1f} seconds")

# Get per-segment durations for subtitles
segment_durations = get_segment_durations()

# Create subtitles
create_subtitles(data, segment_durations)

# Create background music
create_background_music(total_duration + 5, "output/audio/background_music.mp3")

# Assemble final video
assemble_video(data, total_duration)

print(f"\n🎉 Video ready: output/final_video.mp4")
print(f"📸 Thumbnail ready: output/thumbnail.jpg")
```