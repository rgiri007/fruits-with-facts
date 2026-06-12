"""
Step 2: Generate natural voice using Groq TTS (PlayAI Orpheus voices)
- 100% FREE - no credit card required
- Ultra natural voices (Orpheus model)
- Sign up at console.groq.com (email only)
- Add GROQ_API_KEY to GitHub Secrets

SETUP:
1. Go to console.groq.com
2. Sign up with email (no credit card!)
3. Click API Keys → Create API Key
4. Add to GitHub Secrets as GROQ_API_KEY
"""

import json
import os
import subprocess
import sys
import time
import requests


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


def translate_text(text, target_lang):
    if target_lang == "en":
        return text
    url    = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "en", "tl": target_lang, "dt": "t", "q": text}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data       = r.json()
            translated = "".join([chunk[0] for chunk in data[0] if chunk[0]])
            print(f"  Translated: {text[:40]}... → {translated[:40]}...")
            return translated
    except Exception as e:
        print(f"  Translation error: {e}")
    return text


# ── Groq TTS (PlayAI Orpheus) ────────────────────────────────────────────────
# Available voices (all free, all natural):
GROQ_VOICES = {
    # Male voices
    "dan":       "American male, confident and clear",
    "atlas":     "American male, deep and authoritative",
    "orbit":     "American male, warm narrator",
    # Female voices
    "zoe":       "American female, warm and clear",
    "aria":      "American female, energetic and bright",
    "luna":      "American female, calm professional",
    # Other
    "leo":       "American male, casual friendly",
    "nova":      "American female, natural conversational",
}


def groq_tts(text, output_path, voice="dan", api_key=None):
    """
    Groq TTS using PlayAI Orpheus model.
    Free tier, no credit card, ultra natural voices.
    """
    if not api_key:
        print("  No GROQ_API_KEY — skipping Groq TTS")
        return False

    url     = "https://api.groq.com/openai/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json"
    }
    payload = {
        "model": "playai-tts",       # PlayAI Orpheus model on Groq
        "input": text,
        "voice": voice,
        "response_format": "mp3"
    }

    try:
        print(f"  Groq TTS ({voice})...", end=" ", flush=True)
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"HTTP {r.status_code}, {len(r.content)} bytes")

        if r.status_code == 200 and len(r.content) > 1000:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return True

        elif r.status_code == 401:
            print("  Invalid GROQ_API_KEY — check GitHub Secret!")
            return False

        elif r.status_code == 429:
            print("  Rate limited — waiting 30s...")
            time.sleep(30)
            # One retry after rate limit
            r2 = requests.post(url, headers=headers, json=payload, timeout=60)
            if r2.status_code == 200 and len(r2.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(r2.content)
                return True
            return False

        else:
            try:
                print(f"  Error: {r.json()}")
            except:
                print(f"  Error: {r.text[:200]}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"  Connection error: {str(e)[:80]}")
        return False
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {str(e)[:80]}")
        return False


def gtts_fallback(text, output_path, lang="en", tld="com"):
    """gTTS with FFmpeg post-processing to sound more natural"""
    try:
        from gtts import gTTS
        raw_path = output_path.replace(".mp3", "_raw.mp3")

        if lang == "en":
            tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        else:
            tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(raw_path)

        if not os.path.exists(raw_path) or os.path.getsize(raw_path) < 1000:
            return False

        # Post-process: slight pitch up + EQ for more natural sound
        result = subprocess.run([
            "ffmpeg", "-y", "-i", raw_path,
            "-af",
            "asetrate=44100*1.04,"
            "aresample=44100,"
            "atempo=0.96,"
            "equalizer=f=3000:width_type=h:width=2000:g=2",
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            output_path
        ], capture_output=True, timeout=30)

        if os.path.exists(raw_path):
            os.remove(raw_path)

        return result.returncode == 0 and os.path.exists(output_path)

    except Exception as e:
        print(f"  gTTS error: {e}")
        return False


def espeak_fallback(text, output_path):
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


def generate_segment(text, output_path, voice="dan", lang="en", groq_key=None):
    """Try Groq TTS first, fall back to gTTS, then espeak"""

    # Groq TTS (best quality)
    if lang == "en" and groq_key:
        if groq_tts(text, output_path, voice, groq_key):
            return f"groq_{voice}"

    # gTTS fallback (acceptable)
    print(f"  Trying gTTS fallback...")
    if gtts_fallback(text, output_path, lang=lang):
        print(f"  SUCCESS (gTTS)")
        return "gtts"

    # Last resort
    print(f"  WARNING: Using espeak (robotic)")
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
    data   = load_video_data()
    vo     = data["voiceover"]
    fruit  = data["fruit"]

    os.makedirs("output/audio/segments", exist_ok=True)

    # ── VOICE CONFIGURATION ───────────────────────────────────────────────────
    # Groq PlayAI Orpheus voices (very natural):
    # Male:   dan, atlas, orbit, leo
    # Female: zoe, aria, luna, nova
    VOICE_LANG = "en"
    GROQ_KEY   = os.environ.get("GROQ_API_KEY")

    # Alternate voice every video (male/female rotation)
    done_count = 0
    if os.path.exists("fruits_done.txt"):
        with open("fruits_done.txt") as f:
            done_count = sum(1 for l in f if l.strip() and not l.startswith("#"))

    voice_rotation = [
        ("atlas", "American male, deep authoritative"),
        ("zoe",   "American female, warm clear"),
        ("orbit", "American male, warm narrator"),
        ("aria",  "American female, energetic bright"),
    ]
    voice_idx  = done_count % len(voice_rotation)
    VOICE_NAME, voice_desc = voice_rotation[voice_idx]

    print(f"=== Generating voice for: {fruit} ===")
    print(f"Video #{done_count+1} — Voice: {VOICE_NAME} ({voice_desc})")
    if GROQ_KEY:
        print(f"Engine: Groq TTS (PlayAI Orpheus — very natural)")
    else:
        print(f"Engine: gTTS (GROQ_API_KEY not set)")
    print()

    segments = [
        ("hook",   vo["hook"]),
        ("fact_1", f"Fact 1! {vo['fact_1']}"),
        ("fact_2", f"Fact 2! {vo['fact_2']}"),
        ("fact_3", f"Fact 3! {vo['fact_3']}"),
        ("fact_4", f"Fact 4! {vo['fact_4']}"),
        ("fact_5", f"Fact 5! {vo['fact_5']}"),
        ("outro",  vo["outro"]),
    ]

    if VOICE_LANG != "en":
        print(f"Translating to {VOICE_LANG}...")
        segments = [(n, translate_text(t, VOICE_LANG)) for n, t in segments]

    segment_files = []
    methods_used  = []
    for name, text in segments:
        out = f"output/audio/segments/{name}.mp3"
        print(f"\nSegment: {name}")
        method = generate_segment(
            text, out,
            voice=VOICE_NAME,
            lang=VOICE_LANG,
            groq_key=GROQ_KEY
        )
        methods_used.append(method)
        segment_files.append(out)

    duration = combine_audio(segment_files, "output/audio/final_voiceover.mp3")

    print("\n=== Voice Generation Report ===")
    groq_count   = sum(1 for m in methods_used if m.startswith("groq"))
    gtts_count   = methods_used.count("gtts")
    espeak_count = methods_used.count("espeak")
    print(f"Groq TTS (natural):  {groq_count}/{len(segments)}")
    print(f"gTTS (backup):       {gtts_count}/{len(segments)}")
    print(f"espeak (robotic):    {espeak_count}/{len(segments)}")

    if groq_count == len(segments):
        print(f"\nAll segments used natural Groq TTS voice!")
    elif groq_count > 0:
        print(f"\nMostly Groq TTS, some gTTS backup")
    else:
        print(f"\nNo Groq TTS — add GROQ_API_KEY to GitHub Secrets")
        print(f"Get free key at: console.groq.com")

    if duration > 65:
        print(f"\nWARNING: {duration:.1f}s over 60s Shorts limit!")
