"""
Step 4: Assemble interactive YouTube Shorts video (1080x1920)
Optimized for speed on free GitHub Actions runners
"""

import json
import os
import subprocess
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFilter
import textwrap


W, H = 1080, 1920


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


def get_duration(path):
    r = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except:
        return 4.0


def to_srt(s):
    s = max(0.0, s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    ms = int((sec % 1) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{ms:03d}"


# ── Royalty-free music with timeout ──────────────────────────────────────────
def get_background_music(duration):
    out = "output/audio/background_music.mp3"
    trimmed = "output/audio/background_trimmed.mp3"
    os.makedirs("output/audio", exist_ok=True)

    music_urls = [
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d1718ab41b.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a73467.mp3",
    ]

    for url in music_urls:
        try:
            print(f"Downloading music...")
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(out, "wb") as f:
                    f.write(r.content)
                fade_start = max(0, duration - 2)
                subprocess.run([
                    "ffmpeg", "-y", "-i", out, "-t", str(duration + 1),
                    "-af", f"afade=t=out:st={fade_start}:d=2,volume=0.12",
                    "-codec:a", "libmp3lame", trimmed
                ], capture_output=True, timeout=60)
                print("Music ready")
                return trimmed
        except Exception as e:
            print(f"Music URL failed: {e}")
            continue

    # Fast fallback: simple silent track
    print("Using silent music fallback")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(duration + 1),
        "-codec:a", "libmp3lame", trimmed
    ], capture_output=True, timeout=30)
    return trimmed


# ── Create lightweight fact card (much faster than before) ───────────────────
def create_fact_card(fruit_name, fact_num, total_facts, fact_text,
                     emoji, colors, bg_image_path, output_path):
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary, accent = (255,107,53), (255,230,109)

    # Light blur (radius 4 instead of 8 — faster)
    try:
        bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
    except:
        bg = Image.new("RGB", (W, H), primary)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)

    # Top banner
    draw.rectangle([(0, 0), (W, 180)], fill=primary)
    draw.text((W//2, 50),  "🍎 Fruits with Facts", fill=(255,255,255), anchor="mm")
    draw.text((W//2, 120), f"#{fruit_name.replace(' ','')} #Shorts", fill=(255,255,255), anchor="mm")

    # Fact number circle (no glow loop — much faster)
    cy, cr = 580, 160
    draw.ellipse([(W//2-cr, cy-cr), (W//2+cr, cy+cr)], fill=accent)
    draw.text((W//2, cy), f"{fact_num}", fill=(30,30,30), anchor="mm")
    draw.text((W//2, cy + cr + 40), "FACT", fill=accent, anchor="mm")

    # Fact text box
    ty = cy + cr + 120
    th = 420
    draw.rounded_rectangle([(60, ty), (W-60, ty + th)], radius=30, fill=(255,255,255))
    wrapped = textwrap.fill(fact_text, width=28)
    draw.text((W//2, ty + th//2), wrapped, fill=(20,20,20), anchor="mm", align="center")

    # Emoji
    draw.text((W//2, ty + th + 60), emoji * 3, fill=(255,255,255), anchor="mm")

    # Progress dots
    dy = H - 120
    spacing = 60
    total_w = (total_facts - 1) * spacing
    sx = W//2 - total_w//2
    for i in range(total_facts):
        cx = sx + i * spacing
        if i + 1 == fact_num:
            draw.ellipse([(cx-18, dy-18), (cx+18, dy+18)], fill=accent)
        else:
            draw.ellipse([(cx-10, dy-10), (cx+10, dy+10)], fill=(150,150,150))

    card.save(output_path, "PNG", optimize=False)
    return output_path


def create_hook_card(fruit_name, hook_text, emoji, colors, bg_image_path, output_path):
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary, accent = (255,107,53), (255,230,109)

    try:
        bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
    except:
        bg = Image.new("RGB", (W, H), primary)

    overlay = Image.new("RGBA", (W, H), (0,0,0,120))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)
    draw.rectangle([(0,0),(W,160)], fill=primary)
    draw.text((W//2, 80), "🍎 Fruits with Facts", fill=(255,255,255), anchor="mm")
    draw.text((W//2, 680), emoji, fill=(255,255,255), anchor="mm")
    draw.text((W//2, 820), fruit_name.upper(), fill=accent, anchor="mm")
    draw.rounded_rectangle([(200, 920),(880, 1020)], radius=40, fill=accent)
    draw.text((W//2, 970), "5 WILD FACTS!", fill=(30,30,30), anchor="mm")
    draw.rounded_rectangle([(60,1080),(W-60,1380)], radius=25, fill=(255,255,255))
    wrapped = textwrap.fill(hook_text, width=30)
    draw.text((W//2, 1230), wrapped, fill=(20,20,20), anchor="mm", align="center")
    draw.text((W//2, H-120), "👇 Watch till the end!", fill=(255,255,255), anchor="mm")
    card.save(output_path, "PNG", optimize=False)


def create_outro_card(fruit_name, emoji, colors, output_path):
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary, accent = (255,107,53), (255,230,109)

    img = Image.new("RGB", (W, H), primary)
    draw = ImageDraw.Draw(img)
    draw.text((W//2, 400),  "Thanks for watching!", fill=(255,255,255), anchor="mm")
    draw.text((W//2, 650),  emoji * 5,              fill=(255,255,255), anchor="mm")
    draw.text((W//2, 850),  "FOLLOW FOR MORE",      fill=accent,        anchor="mm")
    draw.text((W//2, 980),  "FRUIT FACTS! 🍎",      fill=(255,255,255), anchor="mm")
    draw.rounded_rectangle([(100,1120),(W-100,1260)], radius=40, fill=accent)
    draw.text((W//2, 1190), "👍 LIKE & SUBSCRIBE", fill=(30,30,30), anchor="mm")
    draw.text((W//2, 1380), "Fruits with Facts",    fill=(255,255,255), anchor="mm")
    draw.text((W//2, 1480), "#Shorts #FruitFacts",  fill=(255,255,255), anchor="mm")
    img.save(output_path, "PNG", optimize=False)


# ── Subtitles synced to real audio durations ─────────────────────────────────
def create_subtitles(data):
    vo = data["voiceover"]
    seg_names = ["hook","fact_1","fact_2","fact_3","fact_4","fact_5","outro"]
    seg_texts = [
        vo["hook"],
        f"Fact 1! {vo['fact_1']}",
        f"Fact 2! {vo['fact_2']}",
        f"Fact 3! {vo['fact_3']}",
        f"Fact 4! {vo['fact_4']}",
        f"Fact 5! {vo['fact_5']}",
        vo["outro"],
    ]

    SILENCE = 0.4
    WPL = 6
    srt, idx, cursor = [], 1, 0.0

    for name, text in zip(seg_names, seg_texts):
        seg_path = f"output/audio/segments/{name}.mp3"
        dur = get_duration(seg_path) if os.path.exists(seg_path) \
              else max(2.0, len(text.split()) / 3.0)

        words = text.split()
        chunks = [words[i:i+WPL] for i in range(0, len(words), WPL)]
        card_d = dur / max(len(chunks), 1)

        for chunk in chunks:
            srt.append(
                f"{idx}\n{to_srt(cursor)} --> {to_srt(cursor + card_d - 0.05)}\n"
                f"{' '.join(chunk)}\n"
            )
            idx += 1
            cursor += card_d
        cursor += SILENCE

    srt_path = os.path.abspath("output/subtitles.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt))
    print(f"Subtitles: {idx-1} cards, {cursor:.1f}s total")
    return srt_path, cursor


# ── Build final video — OPTIMIZED FOR SPEED ──────────────────────────────────
def assemble_video(data, srt_path, music_path):
    fruit  = data["fruit"]
    emoji  = data.get("emoji", "🍎")
    colors = data.get("colors", {})
    vo     = data["voiceover"]
    out    = "output/final_video.mp4"

    voiceover_mp3 = "output/audio/final_voiceover.mp3"
    total_dur = get_duration(voiceover_mp3)
    print(f"Duration: {total_dur:.1f}s")

    seg_names = ["hook","fact_1","fact_2","fact_3","fact_4","fact_5","outro"]
    seg_durs  = []
    for name in seg_names:
        p = f"output/audio/segments/{name}.mp3"
        seg_durs.append(get_duration(p) if os.path.exists(p) else 4.0)

    scene_images = [f"output/images/scene_{i}.png" for i in range(1,6)
                    if os.path.exists(f"output/images/scene_{i}.png")]
    if not scene_images:
        scene_images = ["output/images/scene_1.png"]

    # Create cards
    print("Creating cards...")
    os.makedirs("output/cards", exist_ok=True)
    card_paths = []

    create_hook_card(fruit, vo["hook"], emoji, colors, scene_images[0], "output/cards/hook.png")
    card_paths.append(("output/cards/hook.png", seg_durs[0]))

    for i in range(5):
        text = vo[f"fact_{i+1}"]
        img_path = scene_images[i % len(scene_images)]
        card_path = f"output/cards/fact_{i+1}.png"
        create_fact_card(fruit, i+1, 5, text, emoji, colors, img_path, card_path)
        card_paths.append((card_path, seg_durs[i+1]))

    create_outro_card(fruit, emoji, colors, "output/cards/outro.png")
    card_paths.append(("output/cards/outro.png", seg_durs[6]))

    print(f"Created {len(card_paths)} cards")

    # ── FAST FFmpeg command (NO Ken Burns zoom = 3-4x faster) ────────────────
    cmd = ["ffmpeg", "-y"]

    # Each card looped for its duration
    for card_path, dur in card_paths:
        cmd += ["-loop", "1", "-t", str(dur), "-i", card_path]

    cmd += ["-i", voiceover_mp3, "-i", music_path]

    n = len(card_paths)
    vai = n
    mai = n + 1

    # Simple scale (no zoompan filter — that was the bottleneck)
    scale_parts = []
    for i in range(n):
        scale_parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
            f"fps=24,setsar=1[sv{i}]"
        )

    concat_in  = "".join(f"[sv{i}]" for i in range(n))
    concat_out = f"{concat_in}concat=n={n}:v=1:a=0[vconcat]"

    srt_esc = srt_path.replace("\\", "/").replace(":", "\\:")
    sub_style = (
        "FontName=Arial,FontSize=28,Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BackColour=&HAA000000,"
        "BorderStyle=3,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=60,MarginL=40,MarginR=40"
    )
    sub_filter = f"[vconcat]subtitles='{srt_esc}':force_style='{sub_style}'[vout]"

    audio_mix = (
        f"[{vai}:a][{mai}:a]"
        f"amix=inputs=2:weights='1 0.15':duration=first[aout]"
    )

    filter_complex = ";".join(scale_parts + [concat_out, sub_filter, audio_mix])

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "ultrafast",   # was "fast" — now MUCH faster
        "-crf", "26",              # slightly lower quality but tiny visual diff
        "-c:a", "aac",
        "-b:a", "128k",            # was 192k
        "-r", "24",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-shortest",
        "-threads", "0",
        out
    ]

    print("Running FFmpeg (ultrafast preset)...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode == 0:
        size = os.path.getsize(out) / 1024 / 1024
        dur = get_duration(out)
        print(f"Video: {out} ({size:.1f}MB, {dur:.1f}s)")
    else:
        print("FFmpeg error:")
        print(result.stderr[-3000:])
        raise RuntimeError("Video assembly failed")


if __name__ == "__main__":
    data = load_video_data()
    print(f"=== Assembling: {data['fruit']} ===")

    srt_path, _ = create_subtitles(data)
    voiceover_dur = get_duration("output/audio/final_voiceover.mp3")
    music_path = get_background_music(voiceover_dur)
    assemble_video(data, srt_path, music_path)

    print("\nDone!")
