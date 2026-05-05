"""
Step 2: Generate natural voice using gTTS (Google Translate TTS)
- 100% FREE forever (uses Google Translate's TTS endpoint)
- No API key, no signup, no credit card
- Reliable in GitHub Actions (works for 10+ years)
- Natural-sounding voices in many accents
- Used by millions of projects
"""

import json
import os
import subprocess
import sys


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


# ── Generate one segment using gTTS ──────────────────────────────────────────
def gtts_generate(text, output_path, lang="en", tld="com"):
    """
    gTTS uses Google Translate's TTS - completely free and reliable.
    
    Voice options via tld (top-level domain):
      tld="com"  → US English (default, news anchor style)
      tld="co.uk" → British English
      tld="com.au" → Australian English
      tld="ca"   → Canadian English
      tld="co.in" → Indian English
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        tts.save(output_path)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
        else:
            return False
    except Exception as e:
        print(f"  gTTS error: {e}")
        return False


def generate_segment(text, output_path, voice_tld="com"):
    """
    Try gTTS first, only fall back to espeak if completely unavailable.
    """
    print(f"  Generating with gTTS (Google)...")
    if gtts_generate(text, output_path, lang="en", tld=voice_tld):
        print(f"  SUCCESS: {output_path}")
        return "gtts"

    # Try other accents as backup
    for backup_tld in ["co.uk", "com.au", "ca"]:
        if backup_tld == voice_tld:
            continue
        print(f"  Trying backup accent ({backup_tld})...")
        if gtts_generate(text, output_path, lang="en", tld=backup_tld):
            print(f"  SUCCESS with {backup_tld}: {output_path}")
            return "gtts"

    # Final fallback to espeak (should rarely happen with gTTS)
    print(f"  WARNING: gTTS failed entirely, using espeak fallback")
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


# ── Speed up audio slightly to make it more energetic for Shorts ─────────────
def speed_up_audio(input_path, output_path, speed=1.15):
    """Speed up to 115% — sounds more energetic without distorting voice"""
    result = subprocess.run([
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", f"atempo={speed}",
        "-codec:a", "libmp3lame", "-qscale:a", "2",
        output_path
    ], capture_output=True)
    return result.returncode == 0


if __name__ == "__main__":
    data = load_video_data()
    vo = data["voiceover"]
    fruit = data["fruit"]

    os.makedirs("output/audio/segments", exist_ok=True)

    print(f"=== Generating voice for: {fruit} ===")
    print(f"Engine: gTTS (Google) - reliable, natural, free\n")

    # Voice variants you can try by changing the tld:
    #   "com"    → US accent (default)
    #   "co.uk"  → British accent
    #   "com.au" → Australian accent
    #   "co.in"  → Indian accent
    VOICE_TLD = "com"

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
        out_raw = f"output/audio/segments/{name}_raw.mp3"
        out = f"output/audio/segments/{name}.mp3"
        print(f"\nSegment: {name}")
        method = generate_segment(text, out_raw, voice_tld=VOICE_TLD)
        methods_used.append(method)

        # Speed up gTTS audio for energetic Shorts feel
        if method == "gtts":
            if not speed_up_audio(out_raw, out, speed=1.15):
                # If speed-up fails, use raw version
                os.rename(out_raw, out)
            else:
                if os.path.exists(out_raw):
                    os.remove(out_raw)
        else:
            os.rename(out_raw, out)

        segment_files.append(out)

    duration = combine_audio(segment_files, "output/audio/final_voiceover.mp3")

    # Summary
    print("\n=== Voice Generation Report ===")
    gtts_count = methods_used.count("gtts")
    espeak_count = methods_used.count("espeak")
    failed_count = methods_used.count("failed")

    print(f"gTTS (natural):  {gtts_count}/{len(segments)} segments")
    print(f"espeak (robotic): {espeak_count}/{len(segments)} segments")
    print(f"Failed:           {failed_count}/{len(segments)} segments")

    if espeak_count == 0 and failed_count == 0:
        print(f"\nAll segments natural! Total duration: {duration:.1f}s")
    elif espeak_count > 0:
        print("\nWARNING: Some segments fell back to espeak.")
        print("This rarely happens with gTTS — check network in logs above.")

    if duration > 65:
        print(f"WARNING: {duration:.1f}s is over 60s Shorts limit")
