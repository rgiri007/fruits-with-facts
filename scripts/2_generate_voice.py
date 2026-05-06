"""
Step 2: Generate natural voice using StreamElements TTS API
- 100% FREE - no API key, no signup
- Uses Amazon Polly voices (much more natural than gTTS)
- Multiple voice personalities (Brian, Joey, Matthew, etc.)
- Reliable in GitHub Actions
"""

import json
import os
import subprocess
import sys
import requests
import urllib.parse


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


# ── Translate text using Google Translate (free, no API key) ────────────────
def translate_text(text, target_lang):
    if target_lang == "en":
        return text
    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "en", "tl": target_lang, "dt": "t", "q": text}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            translated = "".join([chunk[0] for chunk in data[0] if chunk[0]])
            print(f"  Translated: {text[:40]}... → {translated[:40]}...")
            return translated
    except Exception as e:
        print(f"  Translation error: {e}")
    return text


# ── StreamElements TTS API (FREE, natural Polly voices) ──────────────────────
# Available voices (all FREE):
#   Male:   Brian, Joey, Justin, Matthew, Russell
#   Female: Amy, Emma, Joanna, Ivy, Kendra, Kimberly, Salli, Nicole
STREAMELEMENTS_VOICES = {
    "Brian":    "British male, deep professional",
    "Joey":     "American male, young confident",
    "Matthew":  "American male, mature warm",
    "Justin":   "American male, casual friendly",
    "Russell":  "Australian male, deep",
    "Amy":      "British female, warm",
    "Emma":     "British female, energetic",
    "Joanna":   "American female, professional",
    "Kendra":   "American female, friendly",
    "Salli":    "American female, energetic",
}


def streamelements_tts(text, output_path, voice="Brian"):
    """
    Free StreamElements TTS using Amazon Polly voices.
    No API key, no signup, no rate limit issues.
    """
    url = "https://api.streamelements.com/kappa/v2/speech"
    params = {
        "voice": voice,
        "text": text
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True
        else:
            print(f"  StreamElements error: {r.status_code}")
            return False
    except Exception as e:
        print(f"  StreamElements exception: {e}")
        return False


def gtts_fallback(text, output_path, lang="en", tld="com"):
    """gTTS fallback if StreamElements fails"""
    try:
        from gtts import gTTS
        if lang == "en":
            tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        else:
            tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"  gTTS error: {e}")
        return False


def espeak_fallback(text, output_path):
    """Last-resort fallback (sounds robotic)"""
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


def generate_segment(text, output_path, voice="Brian", lang="en"):
    """
    Try StreamElements first (best quality), fall back as needed.
    Note: StreamElements supports English voices only.
    """
    if lang == "en":
        # Try StreamElements with primary voice
        print(f"  Trying StreamElements ({voice})...")
        if streamelements_tts(text, output_path, voice):
            print(f"  SUCCESS (StreamElements {voice})")
            return f"streamelements_{voice}"

        # Try alternative voices
        for backup in ["Brian", "Joey", "Matthew", "Justin"]:
            if backup == voice:
                continue
            print(f"  Trying StreamElements ({backup})...")
            if streamelements_tts(text, output_path, backup):
                print(f"  SUCCESS (StreamElements {backup})")
                return f"streamelements_{backup}"

        # gTTS fallback
        print(f"  Trying gTTS fallback...")
        if gtts_fallback(text, output_path):
            print(f"  SUCCESS (gTTS)")
            return "gtts"
    else:
        # Non-English: gTTS supports many languages, StreamElements doesn't
        print(f"  Using gTTS for {lang}...")
        if gtts_fallback(text, output_path, lang=lang):
            print(f"  SUCCESS (gTTS {lang})")
            return "gtts"

    # Last resort
    print(f"  WARNING: Using espeak (will sound robotic)")
    if espeak_fallback(text, output_path):
        return "espeak"
    return "failed"


def combine_audio(segment_files, output_path):
    os.makedirs("output/audio", exist_ok=True)

    silence = "output/audio/silence.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", "0.25", "-codec:a", "libmp3lame", silence
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

    # ── VOICE CONFIGURATION ───────────────────────────────────────────────────
    # English voices (StreamElements - natural Polly):
    #   Brian, Joey, Matthew, Justin, Russell  (male)
    #   Amy, Emma, Joanna, Kendra, Salli        (female)
    VOICE_NAME = "Matthew"   # Warm mature male voice (best for facts)

    # Language for spoken audio:
    #   "en" → English (uses StreamElements)
    #   "ne" → Nepali (uses gTTS)
    #   "hi" → Hindi (uses gTTS)
    VOICE_LANG = "en"

    print(f"=== Generating voice for: {fruit} ===")
    print(f"Engine: StreamElements (Amazon Polly voices)")
    print(f"Voice: {VOICE_NAME} ({STREAMELEMENTS_VOICES.get(VOICE_NAME, 'N/A')})\n")

    segments = [
        ("hook",   vo["hook"]),
        ("fact_1", f"Fact 1! {vo['fact_1']}"),
        ("fact_2", f"Fact 2! {vo['fact_2']}"),
        ("fact_3", f"Fact 3! {vo['fact_3']}"),
        ("fact_4", f"Fact 4! {vo['fact_4']}"),
        ("fact_5", f"Fact 5! {vo['fact_5']}"),
        ("outro",  vo["outro"]),
    ]

    # Translate if non-English
    if VOICE_LANG != "en":
        print(f"Translating to {VOICE_LANG}...")
        segments = [(name, translate_text(text, VOICE_LANG)) for name, text in segments]
        print()

    segment_files = []
    methods_used = []
    for name, text in segments:
        out = f"output/audio/segments/{name}.mp3"
        print(f"\nSegment: {name}")
        method = generate_segment(text, out, voice=VOICE_NAME, lang=VOICE_LANG)
        methods_used.append(method)
        segment_files.append(out)

    duration = combine_audio(segment_files, "output/audio/final_voiceover.mp3")

    # Summary
    print("\n=== Voice Generation Report ===")
    se_count = sum(1 for m in methods_used if m.startswith("streamelements"))
    gtts_count = methods_used.count("gtts")
    espeak_count = methods_used.count("espeak")

    print(f"StreamElements (natural):  {se_count}/{len(segments)}")
    print(f"gTTS (backup):             {gtts_count}/{len(segments)}")
    print(f"espeak (robotic):          {espeak_count}/{len(segments)}")

    if espeak_count > 0:
        print("\nWARNING: Some segments fell back to espeak!")
    elif se_count == len(segments):
        print(f"\nAll segments used natural StreamElements voice!")

    if duration > 65:
        print(f"WARNING: {duration:.1f}s is over 60s Shorts limit")
