“””
Step 2: Generate voiceover using espeak-ng
100% FREE - No account - No API key - No credit card - Built into Linux
espeak-ng is pre-installed on GitHub Actions Ubuntu runners
Produces clear robotic-style narration, perfect for faceless YouTube videos
“””

import json
import os
import subprocess
import time

# ── Load video data ───────────────────────────────────────────────────────────

def load_video_data():
with open(“output/video_data.json”, “r”) as f:
return json.load(f)

# ── Generate speech for one segment ──────────────────────────────────────────

def text_to_speech(text, output_path):
“””
espeak-ng: free, offline, no account, pre-installed on Ubuntu/GitHub Actions
Voice options: en-us+f3 (female), en-us+m3 (male), en-gb (British)
“””
wav_path = output_path.replace(”.mp3”, “.wav”)

```
# Generate WAV with espeak-ng
result = subprocess.run([
    "espeak-ng",
    "-v", "en-us+f3",   # Clear female voice
    "-s", "148",         # Speed: words per minute (145-155 sounds natural)
    "-p", "52",          # Pitch (50 = neutral, higher = more expressive)
    "-a", "180",         # Amplitude/volume
    "-g", "8",           # Word gap in ms (adds natural pauses)
    "-w", wav_path,      # Output WAV file
    text
], capture_output=True)

if result.returncode != 0:
    print(f"  espeak error: {result.stderr.decode()}")
    return False

# Convert WAV to MP3 using FFmpeg (better compression)
result2 = subprocess.run([
    "ffmpeg", "-y",
    "-i", wav_path,
    "-codec:a", "libmp3lame",
    "-qscale:a", "2",          # High quality MP3
    "-ar", "44100",            # Sample rate
    output_path
], capture_output=True)

# Clean up WAV file
if os.path.exists(wav_path):
    os.remove(wav_path)

if result2.returncode == 0:
    print(f"  Audio saved: {output_path}")
    return True
else:
    print(f"  FFmpeg error: {result2.stderr.decode()[:200]}")
    return False
```

# ── Combine all audio segments with pauses ────────────────────────────────────

def combine_audio(segment_files, output_path):
os.makedirs(“output/audio”, exist_ok=True)

```
# Create a short silence file (0.8 seconds between facts)
silence_path = "output/audio/silence.mp3"
subprocess.run([
    "ffmpeg", "-y",
    "-f", "lavfi",
    "-i", "anullsrc=r=44100:cl=mono",
    "-t", "0.8",
    "-codec:a", "libmp3lame",
    silence_path
], capture_output=True)

# Build concat list with silence between each segment
list_file = "output/audio/concat_list.txt"
with open(list_file, "w") as f:
    for i, seg in enumerate(segment_files):
        # Use absolute-safe relative path
        f.write(f"file '../../{seg}'\n")
        if i < len(segment_files) - 1:
            f.write("file 'silence.mp3'\n")

# Concatenate all segments
result = subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", list_file,
    "-codec:a", "libmp3lame",
    "-qscale:a", "2",
    output_path
], capture_output=True)

if result.returncode == 0:
    # Get duration
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_path
    ], capture_output=True, text=True)
    duration = float(probe.stdout.strip() or "0")
    print(f"Combined audio saved: {output_path} ({duration:.1f}s)")
else:
    print(f"Combine error: {result.stderr.decode()[:300]}")
```

# ── Main ──────────────────────────────────────────────────────────────────────

if **name** == “**main**”:
data = load_video_data()
voiceover = data[“voiceover”]
fruit_name = data[“fruit”]

```
os.makedirs("output/audio/segments", exist_ok=True)

print(f"Generating voice for: {fruit_name}")
print("Using espeak-ng (free, no account needed)")

segments = [
    ("intro",  voiceover["intro"]),
    ("fact_1", voiceover["fact_1"]),
    ("fact_2", voiceover["fact_2"]),
    ("fact_3", voiceover["fact_3"]),
    ("fact_4", voiceover["fact_4"]),
    ("fact_5", voiceover["fact_5"]),
    ("outro",  voiceover["outro"]),
]

segment_files = []
for name, text in segments:
    out_path = f"output/audio/segments/{name}.mp3"
    print(f"Generating: {name}")
    success = text_to_speech(text, out_path)
    if not success:
        print(f"WARNING: Failed to generate {name}")
    segment_files.append(out_path)

combine_audio(segment_files, "output/audio/final_voiceover.mp3")
print("\nAll voice segments done!")
```