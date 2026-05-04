"""
Step 4: Assemble interactive colourful YouTube Shorts video (1080x1920)
Features:
  - Animated fact cards with colourful backgrounds
  - Ken Burns zoom effect on images
  - Bold colourful subtitles synced to voice
  - Royalty-free background music from Pixabay
  - Progress indicator (Fact 1/5, 2/5...)
  - Max 60 seconds
"""

import json
import os
import subprocess
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import textwrap


W, H = 1080, 1920  # Shorts vertical format


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


# ── Download royalty-free music from Pixabay ─────────────────────────────────
def get_background_music(duration):
    out = "output/audio/background_music.mp3"

    # Curated list of royalty-free Pixabay music URLs
    # These are free for commercial use, no attribution needed
    music_urls = [
        "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d1718ab41b.mp3",
        "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8c8a73467.mp3",
        "https://cdn.pixabay.com/download/audio/2021/11/13/audio_cb4f6a4a04.mp3",
    ]

    for url in music_urls:
        try:
            print(f"  Downloading background music...")
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and len(r.content) > 10000:
                with open(out, "wb") as f:
                    f.write(r.content)
                print(f"  Music downloaded: {out}")

                # Trim to video duration + fade out
                trimmed = "output/audio/background_trimmed.mp3"
                subprocess.run([
                    "ffmpeg", "-y", "-i", out,
                    "-t", str(duration + 1),
                    "-af", f"afade=t=out:st={max(0,duration-2)}:d=2,volume=0.12",
                    "-codec:a", "libmp3lame", trimmed
                ], capture_output=True)
                return trimmed
        except Exception as e:
            print(f"  Music URL failed: {e}")
            continue

    # Fallback: generate gentle ambient tone
    print("  Using generated ambient music fallback")
    fade_start = max(0, duration - 2)
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=44100",
        "-f", "lavfi", "-i", "sine=frequency=330:sample_rate=44100",
        "-filter_complex",
        f"[0][1]amix=inputs=2:duration=longest,"
        f"volume=0.08,afade=t=in:d=2,afade=t=out:st={fade_start}:d=2",
        "-t", str(duration + 1),
        "-codec:a", "libmp3lame",
        "output/audio/background_trimmed.mp3"
    ], capture_output=True)
    return "output/audio/background_trimmed.mp3"


# ── Create animated fact card image ──────────────────────────────────────────
def create_fact_card(fruit_name, fact_num, total_facts, fact_text,
                     emoji, colors, bg_image_path, output_path):
    """
    Creates a colourful animated-style card for each fact:
    - Blurred fruit image as background
    - Vibrant colour overlay
    - Large fact number display
    - Fact text with emoji
    - Progress dots
    """
    # Parse colors from Gemini output
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary = (255, 107, 53)
        accent  = (255, 230, 109)

    # Load and blur background image
    try:
        bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=8))
    except:
        bg = Image.new("RGB", (W, H), primary)

    # Semi-transparent dark overlay for readability
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)

    # Vibrant top banner
    banner_h = 180
    draw.rectangle([(0, 0), (W, banner_h)], fill=primary)

    # Channel name in banner
    draw.text((W//2, 50), "🍎 Fruits with Facts",
              fill=(255,255,255), anchor="mm")
    draw.text((W//2, 120), f"#{fruit_name.replace(' ','')} #Shorts",
              fill=(255,255,255), anchor="mm")

    # Giant fact number in the middle
    fact_circle_y = 580
    circle_r = 160
    # Draw glowing circle
    for glow in range(5, 0, -1):
        glow_color = (*accent, 40 * glow)
        glow_img = Image.new("RGBA", (W, H), (0,0,0,0))
        glow_draw = ImageDraw.Draw(glow_img)
        glow_draw.ellipse([
            (W//2 - circle_r - glow*8, fact_circle_y - circle_r - glow*8),
            (W//2 + circle_r + glow*8, fact_circle_y + circle_r + glow*8)
        ], fill=glow_color)
        card = Image.alpha_composite(card.convert("RGBA"), glow_img).convert("RGB")
        draw = ImageDraw.Draw(card)

    draw.ellipse([
        (W//2 - circle_r, fact_circle_y - circle_r),
        (W//2 + circle_r, fact_circle_y + circle_r)
    ], fill=accent)

    draw.text((W//2, fact_circle_y), f"{fact_num}", fill=(30,30,30), anchor="mm")
    draw.text((W//2, fact_circle_y + circle_r + 40), "FACT", fill=accent, anchor="mm")

    # Fact text box
    text_y = fact_circle_y + circle_r + 120
    text_box_h = 420
    draw.rounded_rectangle(
        [(60, text_y), (W-60, text_y + text_box_h)],
        radius=30, fill=(255,255,255,230)
    )

    # Wrap and draw fact text
    wrapped = textwrap.fill(fact_text, width=28)
    draw.text((W//2, text_y + text_box_h//2), wrapped,
              fill=(20,20,20), anchor="mm", align="center")

    # Emoji display
    draw.text((W//2, text_y + text_box_h + 60), emoji * 3,
              fill=(255,255,255), anchor="mm")

    # Progress dots at bottom
    dot_y = H - 120
    dot_spacing = 60
    total_width = (total_facts - 1) * dot_spacing
    start_x = W//2 - total_width//2

    for i in range(total_facts):
        cx = start_x + i * dot_spacing
        if i + 1 == fact_num:
            # Active dot — large and bright
            draw.ellipse([(cx-18, dot_y-18), (cx+18, dot_y+18)], fill=accent)
        else:
            # Inactive dot
            draw.ellipse([(cx-10, dot_y-10), (cx+10, dot_y+10)], fill=(150,150,150))

    card.save(output_path, "PNG", quality=95)
    return output_path


# ── Create hook card (opening frame) ─────────────────────────────────────────
def create_hook_card(fruit_name, hook_text, emoji, colors, bg_image_path, output_path):
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary = (255, 107, 53)
        accent  = (255, 230, 109)

    try:
        bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=3))
    except:
        bg = Image.new("RGB", (W, H), primary)

    overlay = Image.new("RGBA", (W, H), (0,0,0,120))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)

    # Top bar
    draw.rectangle([(0,0),(W,160)], fill=primary)
    draw.text((W//2, 80), "🍎 Fruits with Facts", fill=(255,255,255), anchor="mm")

    # Big emoji
    draw.text((W//2, 680), emoji, fill=(255,255,255), anchor="mm")

    # Fruit name
    draw.text((W//2, 820), fruit_name.upper(), fill=accent, anchor="mm")

    # "5 FACTS" badge
    draw.rounded_rectangle([(200, 920),(880, 1020)], radius=40, fill=accent)
    draw.text((W//2, 970), "5 WILD FACTS!", fill=(30,30,30), anchor="mm")

    # Hook text
    wrapped = textwrap.fill(hook_text, width=30)
    draw.rounded_rectangle([(60,1080),(W-60,1380)], radius=25, fill=(255,255,255,220))
    draw.text((W//2, 1230), wrapped, fill=(20,20,20), anchor="mm", align="center")

    # Swipe hint
    draw.text((W//2, H-120), "👇 Watch till the end!", fill=(255,255,255), anchor="mm")

    card.save(output_path, "PNG", quality=95)


# ── Create outro card ─────────────────────────────────────────────────────────
def create_outro_card(fruit_name, emoji, colors, output_path):
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary = (255, 107, 53)
        accent  = (255, 230, 109)

    img = Image.new("RGB", (W, H), primary)
    draw = ImageDraw.Draw(img)

    # Gradient effect
    for i in range(H):
        ratio = i / H
        r = int(primary[0]*(1-ratio) + max(0,primary[0]-60)*ratio)
        g = int(primary[1]*(1-ratio) + max(0,primary[1]-60)*ratio)
        b = int(primary[2]*(1-ratio) + max(0,primary[2]-60)*ratio)
        draw.line([(0,i),(W,i)], fill=(r,g,b))

    draw.text((W//2, 400),  "Thanks for watching!", fill=(255,255,255), anchor="mm")
    draw.text((W//2, 650),  emoji * 5,              fill=(255,255,255), anchor="mm")
    draw.text((W//2, 850),  "FOLLOW FOR MORE",      fill=accent,        anchor="mm")
    draw.text((W//2, 980),  "FRUIT FACTS! 🍎",      fill=(255,255,255), anchor="mm")

    draw.rounded_rectangle([(100,1120),(W-100,1260)], radius=40, fill=accent)
    draw.text((W//2, 1190), "👍 LIKE & SUBSCRIBE", fill=(30,30,30), anchor="mm")

    draw.text((W//2, 1380), "Fruits with Facts",    fill=(255,255,255), anchor="mm")
    draw.text((W//2, 1480), "#Shorts #FruitFacts",  fill=(255,255,255,180), anchor="mm")

    img.save(output_path, "PNG", quality=95)


# ── Build SRT subtitles from real audio durations ─────────────────────────────
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
    WORDS_PER_LINE = 6
    srt, idx, cursor = [], 1, 0.0

    for name, text in zip(seg_names, seg_texts):
        seg_path = f"output/audio/segments/{name}.mp3"
        dur = get_duration(seg_path) if os.path.exists(seg_path) \
              else max(2.0, len(text.split()) / 3.0)

        words  = text.split()
        chunks = [words[i:i+WORDS_PER_LINE] for i in range(0, len(words), WORDS_PER_LINE)]
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


# ── Assemble final Shorts video ───────────────────────────────────────────────
def assemble_video(data, srt_path, music_path):
    fruit   = data["fruit"]
    emoji   = data.get("emoji", "🍎")
    colors  = data.get("colors", {})
    vo      = data["voiceover"]
    out_mp4 = "output/final_video.mp4"

    voiceover_mp3 = "output/audio/final_voiceover.mp3"
    total_dur = get_duration(voiceover_mp3)
    print(f"Total duration: {total_dur:.1f}s")

    # Get segment durations
    seg_names = ["hook","fact_1","fact_2","fact_3","fact_4","fact_5","outro"]
    seg_durs  = []
    for name in seg_names:
        p = f"output/audio/segments/{name}.mp3"
        seg_durs.append(get_duration(p) if os.path.exists(p) else 4.0)

    # Get scene images
    scene_images = [f"output/images/scene_{i}.png" for i in range(1,6)
                    if os.path.exists(f"output/images/scene_{i}.png")]
    if not scene_images:
        scene_images = ["output/images/scene_1.png"]

    # ── Create animated cards for each segment ────────────────────────────────
    print("Creating animated fact cards...")
    os.makedirs("output/cards", exist_ok=True)

    card_paths = []

    # Hook card
    hook_path = "output/cards/hook.png"
    create_hook_card(fruit, vo["hook"], emoji, colors,
                     scene_images[0], hook_path)
    card_paths.append((hook_path, seg_durs[0]))

    # Fact cards 1-5
    fact_texts = [vo[f"fact_{i}"] for i in range(1,6)]
    for i, (text, dur) in enumerate(zip(fact_texts, seg_durs[1:6])):
        img_path = scene_images[i % len(scene_images)]
        card_path = f"output/cards/fact_{i+1}.png"
        create_fact_card(fruit, i+1, 5, text, emoji, colors, img_path, card_path)
        card_paths.append((card_path, dur))

    # Outro card
    outro_path = "output/cards/outro.png"
    create_outro_card(fruit, emoji, colors, outro_path)
    card_paths.append((outro_path, seg_durs[6]))

    # ── Build FFmpeg command ──────────────────────────────────────────────────
    cmd = ["ffmpeg", "-y"]

    # Input: each card image looped for its duration with Ken Burns zoom
    n = len(card_paths)
    for card_path, dur in card_paths:
        cmd += ["-loop", "1", "-t", str(dur), "-i", card_path]

    # Audio inputs
    cmd += ["-i", voiceover_mp3, "-i", music_path]

    vai = n      # voiceover index
    mai = n + 1  # music index

    # Scale + Ken Burns zoom effect on each card
    scale_parts = []
    for i in range(n):
        # Gentle zoom in effect — starts at 100% ends at 108%
        zoom_expr = (
            f"[{i}:v]"
            f"scale=8000:-1,"
            f"zoompan=z='min(zoom+0.0008,1.08)':d={int(card_paths[i][1]*25)}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={W}x{H}:fps=25,"
            f"setsar=1[sv{i}]"
        )
        scale_parts.append(zoom_expr)

    # Concat all cards → [vconcat]
    concat_in  = "".join(f"[sv{i}]" for i in range(n))
    concat_out = f"{concat_in}concat=n={n}:v=1:a=0[vconcat]"

    # Burn subtitles into video → [vout]
    srt_esc = srt_path.replace("\\", "/").replace(":", "\\:")
    sub_style = (
        "FontName=Arial,FontSize=28,Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BackColour=&HAA000000,"
        "BorderStyle=3,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=60,MarginL=40,MarginR=40"
    )
    sub_filter = (
        f"[vconcat]subtitles='{srt_esc}':"
        f"force_style='{sub_style}'[vout]"
    )

    # Mix audio → [aout]
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
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-r", "25",
        "-movflags", "+faststart",
        "-shortest",
        out_mp4
    ]

    print("Assembling Shorts video (this takes 2-3 minutes)...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        size_mb = os.path.getsize(out_mp4) / 1024 / 1024
        dur = get_duration(out_mp4)
        print(f"Video ready: {out_mp4} ({size_mb:.1f}MB, {dur:.1f}s)")
        if dur > 62:
            print(f"WARNING: {dur:.1f}s is over 60s Shorts limit!")
    else:
        print("FFmpeg error:")
        print(result.stderr[-3000:])
        raise RuntimeError("Video assembly failed")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = load_video_data()
    print(f"=== Assembling Shorts for: {data['fruit']} ===")

    # 1. Subtitles
    srt_path, total_dur = create_subtitles(data)

    # 2. Background music
    voiceover_dur = get_duration("output/audio/final_voiceover.mp3")
    music_path = get_background_music(voiceover_dur)

    # 3. Assemble
    assemble_video(data, srt_path, music_path)

    print("\nDone!")
    print("  output/final_video.mp4  — Shorts ready!")
    print("  output/thumbnail.jpg    — Thumbnail ready!")
