"""
Step 4: Assemble interactive YouTube Shorts video (1080x1920)
With cinematic animations: Ken Burns zoom, pan effects, fade transitions
Makes images feel like real video clips!
"""

import json
import os
import subprocess
import requests
import urllib.parse
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import textwrap
import random


W, H = 1080, 1920
FPS = 30  # Higher fps = smoother animations


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


# ── Royalty-free music ───────────────────────────────────────────────────────
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

    # Silent fallback
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(duration + 1),
        "-codec:a", "libmp3lame", trimmed
    ], capture_output=True, timeout=30)
    return trimmed


# ── Create lightweight fact card ──────────────────────────────────────────────
def create_fact_card(fruit_name, fact_num, total_facts, fact_text,
                     emoji, colors, bg_image_path, output_path):
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary, accent = (255,107,53), (255,230,109)

    try:
        bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
    except:
        bg = Image.new("RGB", (W, H), primary)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
    card = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(card)

    draw.rectangle([(0, 0), (W, 180)], fill=primary)
    draw.text((W//2, 50),  "🍎 Fruits with Facts", fill=(255,255,255), anchor="mm")
    draw.text((W//2, 120), f"#{fruit_name.replace(' ','')} #Shorts", fill=(255,255,255), anchor="mm")

    cy, cr = 580, 160
    draw.ellipse([(W//2-cr, cy-cr), (W//2+cr, cy+cr)], fill=accent)
    draw.text((W//2, cy), f"{fact_num}", fill=(30,30,30), anchor="mm")
    draw.text((W//2, cy + cr + 40), "FACT", fill=accent, anchor="mm")

    ty = cy + cr + 120
    th = 420
    draw.rounded_rectangle([(60, ty), (W-60, ty + th)], radius=30, fill=(255,255,255))
    wrapped = textwrap.fill(fact_text, width=28)
    draw.text((W//2, ty + th//2), wrapped, fill=(20,20,20), anchor="mm", align="center")

    draw.text((W//2, ty + th + 60), emoji * 3, fill=(255,255,255), anchor="mm")

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


# ── Subtitles ────────────────────────────────────────────────────────────────
def create_subtitles(data, thumbnail_offset=1.5):
    """thumbnail_offset = seconds added at start for the thumbnail card"""
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
    srt, idx = [], 1
    cursor = thumbnail_offset  # account for thumbnail intro

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


# ── Build animation filter for each card ─────────────────────────────────────
def build_animation_filter(input_idx, duration, anim_type, output_label):
    """
    Returns a FFmpeg filter string that animates a still image.
    
    Animation types (cycled across cards for variety):
      - zoom_in:    slow zoom from 1.0x → 1.15x (Ken Burns)
      - zoom_out:   slow zoom from 1.15x → 1.0x
      - pan_left:   pan from right to left
      - pan_right:  pan from left to right
      - pan_up:     pan from bottom to top
      - zoom_pan:   zoom while panning diagonally
    """
    total_frames = int(duration * FPS)

    # Higher upscale = smoother zoompan motion
    upscale = 4000

    if anim_type == "zoom_in":
        # Ken Burns classic: slow zoom in, centered
        filter_str = (
            f"[{input_idx}:v]"
            f"scale={upscale}:-1,"
            f"zoompan="
            f"z='min(zoom+0.0015,1.15)':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:"
            f"s={W}x{H}:fps={FPS},"
            f"setsar=1[{output_label}]"
        )

    elif anim_type == "zoom_out":
        # Reverse Ken Burns: zoom out from close-up
        filter_str = (
            f"[{input_idx}:v]"
            f"scale={upscale}:-1,"
            f"zoompan="
            f"z='if(eq(on,0),1.15,max(zoom-0.0015,1.0))':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:"
            f"s={W}x{H}:fps={FPS},"
            f"setsar=1[{output_label}]"
        )

    elif anim_type == "pan_left":
        # Slow horizontal pan right→left, slight zoom
        filter_str = (
            f"[{input_idx}:v]"
            f"scale={upscale}:-1,"
            f"zoompan="
            f"z='1.1':"
            f"x='iw-(iw/zoom)-(on*(iw-(iw/zoom))/{total_frames})':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:"
            f"s={W}x{H}:fps={FPS},"
            f"setsar=1[{output_label}]"
        )

    elif anim_type == "pan_right":
        # Slow horizontal pan left→right
        filter_str = (
            f"[{input_idx}:v]"
            f"scale={upscale}:-1,"
            f"zoompan="
            f"z='1.1':"
            f"x='(on*(iw-(iw/zoom))/{total_frames})':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:"
            f"s={W}x{H}:fps={FPS},"
            f"setsar=1[{output_label}]"
        )

    elif anim_type == "pan_up":
        # Vertical pan bottom→top
        filter_str = (
            f"[{input_idx}:v]"
            f"scale={upscale}:-1,"
            f"zoompan="
            f"z='1.1':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih-(ih/zoom)-(on*(ih-(ih/zoom))/{total_frames})':"
            f"d={total_frames}:"
            f"s={W}x{H}:fps={FPS},"
            f"setsar=1[{output_label}]"
        )

    else:  # zoom_pan default — zoom + diagonal pan
        filter_str = (
            f"[{input_idx}:v]"
            f"scale={upscale}:-1,"
            f"zoompan="
            f"z='min(zoom+0.001,1.12)':"
            f"x='(on*(iw-(iw/zoom))/{total_frames})':"
            f"y='(on*(ih-(ih/zoom))/{total_frames})':"
            f"d={total_frames}:"
            f"s={W}x{H}:fps={FPS},"
            f"setsar=1[{output_label}]"
        )

    return filter_str


# ── Assemble video with cinematic animations ─────────────────────────────────
def assemble_video(data, srt_path, music_path):
    fruit  = data["fruit"]
    emoji  = data.get("emoji", "🍎")
    colors = data.get("colors", {})
    vo     = data["voiceover"]
    out    = "output/final_video.mp4"

    voiceover_mp3_orig = "output/audio/final_voiceover.mp3"
    voiceover_mp3 = "output/audio/voiceover_with_intro.mp3"

    # Add 1.5s silence at start to sync with thumbnail card
    THUMB_DURATION = 1.5
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-i", voiceover_mp3_orig,
        "-filter_complex",
        f"[0:a]atrim=0:{THUMB_DURATION}[silence];[silence][1:a]concat=n=2:v=0:a=1[out]",
        "-map", "[out]",
        "-codec:a", "libmp3lame", "-qscale:a", "2",
        voiceover_mp3
    ], capture_output=True, timeout=60)

    if not os.path.exists(voiceover_mp3) or os.path.getsize(voiceover_mp3) < 1000:
        voiceover_mp3 = voiceover_mp3_orig

    total_dur = get_duration(voiceover_mp3)
    print(f"Duration: {total_dur:.1f}s")

    # Get audio segment durations
    seg_names = ["hook","fact_1","fact_2","fact_3","fact_4","fact_5","outro"]
    seg_durs = []
    for name in seg_names:
        p = f"output/audio/segments/{name}.mp3"
        seg_durs.append(get_duration(p) if os.path.exists(p) else 4.0)

    # Get fruit images
    scene_images = [f"output/images/scene_{i}.png" for i in range(1,6)
                    if os.path.exists(f"output/images/scene_{i}.png")]
    if not scene_images:
        scene_images = ["output/images/scene_1.png"]

    # ── Create cards ──────────────────────────────────────────────────────────
    print("Creating animated cards...")
    os.makedirs("output/cards", exist_ok=True)

    # Each card has: (image_path, duration, animation_type)
    # Animation types cycle for variety
    animation_cycle = ["zoom_in", "pan_right", "zoom_pan", "pan_left", "zoom_out", "pan_up", "zoom_in"]
    card_paths = []

    # 1. Thumbnail intro card (1.5s) with zoom_in animation
    thumb_vertical = "output/thumbnail_vertical.png"
    if os.path.exists(thumb_vertical):
        card_paths.append((thumb_vertical, THUMB_DURATION, "zoom_in"))
        print("  Added thumbnail as opening frame (zoom_in)")

    # 2. Hook card (with first scene image as bg)
    create_hook_card(fruit, vo["hook"], emoji, colors, scene_images[0], "output/cards/hook.png")
    card_paths.append(("output/cards/hook.png", seg_durs[0], "zoom_out"))

    # 3. 5 fact cards, each with different animation
    for i in range(5):
        text = vo[f"fact_{i+1}"]
        img_path = scene_images[i % len(scene_images)]
        card_path = f"output/cards/fact_{i+1}.png"
        create_fact_card(fruit, i+1, 5, text, emoji, colors, img_path, card_path)
        anim = animation_cycle[(i+1) % len(animation_cycle)]
        card_paths.append((card_path, seg_durs[i+1], anim))

    # 4. Outro card with zoom_in
    create_outro_card(fruit, emoji, colors, "output/cards/outro.png")
    card_paths.append(("output/cards/outro.png", seg_durs[6], "zoom_in"))

    print(f"Created {len(card_paths)} animated cards")

    # ── Build FFmpeg command ──────────────────────────────────────────────────
    cmd = ["ffmpeg", "-y"]

    # Image inputs (each looped for its duration)
    for card_path, dur, anim in card_paths:
        cmd += ["-loop", "1", "-t", str(dur), "-i", card_path]

    cmd += ["-i", voiceover_mp3, "-i", music_path]

    n = len(card_paths)
    vai = n      # voiceover audio index
    mai = n + 1  # music audio index

    # Build animation filter for each card
    anim_parts = []
    for i, (card_path, dur, anim_type) in enumerate(card_paths):
        anim_parts.append(
            build_animation_filter(i, dur, anim_type, f"sv{i}")
        )

    # Concat all animated streams
    concat_in  = "".join(f"[sv{i}]" for i in range(n))
    concat_out = f"{concat_in}concat=n={n}:v=1:a=0[vconcat]"

    # Burn subtitles
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

    # Audio mix
    audio_mix = (
        f"[{vai}:a][{mai}:a]"
        f"amix=inputs=2:weights='1 0.15':duration=first[aout]"
    )

    filter_complex = ";".join(anim_parts + [concat_out, sub_filter, audio_mix])

    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",      # 'fast' for animations - 'ultrafast' breaks zoompan
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", str(FPS),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-shortest",
        "-threads", "0",
        out
    ]

    print(f"Running FFmpeg with {n} animated segments at {FPS}fps...")
    print("(this takes 8-15 minutes for cinematic animations)")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1500)

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
    print(f"=== Assembling animated video for: {data['fruit']} ===")

    # Subtitles offset by 1.5s for thumbnail intro
    srt_path, _ = create_subtitles(data, thumbnail_offset=1.5)

    voiceover_dur = get_duration("output/audio/final_voiceover.mp3") + 1.5
    music_path = get_background_music(voiceover_dur)
    assemble_video(data, srt_path, music_path)

    print("\nDone!")
