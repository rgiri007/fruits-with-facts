"""
Step 3: Generate fruit images + BEAUTIFUL eye-catching thumbnail
Uses Pollinations AI (free) for fruit photos
Creates colorful thumbnail with "5 FACTS" text overlay
"""

import json
import os
import time
import requests
from PIL import Image, ImageDraw, ImageFilter
import io
import urllib.parse


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


def generate_image(prompt, output_path, index, width=1080, height=1920):
    enhanced = (
        f"{prompt}, ultra realistic, vibrant colors, "
        "professional photography, high detail, 4k"
    )
    encoded = urllib.parse.quote(enhanced)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&seed={index*77}&nologo=true&enhance=true"
    )

    for attempt in range(3):
        try:
            print(f"  Image {index+1} (attempt {attempt+1})...")
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 1000:
                img = Image.open(io.BytesIO(r.content))
                img = img.resize((width, height), Image.LANCZOS)
                img.save(output_path, "PNG", quality=95)
                print(f"  Saved: {output_path}")
                return True
            time.sleep(10)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(10)

    return create_fallback_image(output_path, index, width, height)


def create_fallback_image(output_path, index, width, height):
    gradients = [
        [(255,107,53),(255,180,50)],
        [(50,205,50),(0,168,107)],
        [(255,20,147),(255,105,180)],
        [(100,149,237),(65,105,225)],
        [(255,215,0),(255,140,0)],
    ]
    c = gradients[index % len(gradients)]
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for i in range(height):
        ratio = i / height
        r = int(c[0][0]*(1-ratio) + c[1][0]*ratio)
        g = int(c[0][1]*(1-ratio) + c[1][1]*ratio)
        b = int(c[0][2]*(1-ratio) + c[1][2]*ratio)
        draw.line([(0,i),(width,i)], fill=(r,g,b))
    img.save(output_path, "PNG")
    print(f"  Fallback saved: {output_path}")
    return True


# ── Generate a stunning eye-catching thumbnail ────────────────────────────────
def create_beautiful_thumbnail(fruit_name, emoji, colors, image_paths,
                               output_path, vertical_path):
    """
    Creates 2 thumbnails:
    1. YouTube-standard 1280x720 (horizontal) for video metadata
    2. 1080x1920 (vertical) used as the FIRST FRAME of Shorts video
       — this is what users actually see when scrolling Shorts!
    """
    try:
        primary = tuple(int(colors.get("primary","#FF6B35").lstrip("#")[i:i+2],16) for i in (0,2,4))
        accent  = tuple(int(colors.get("accent", "#FFE66D").lstrip("#")[i:i+2],16) for i in (0,2,4))
        secondary = tuple(int(colors.get("secondary","#C44A1F").lstrip("#")[i:i+2],16) for i in (0,2,4))
    except:
        primary, accent, secondary = (255,107,53), (255,230,109), (196,74,31)

    # ── 1. Vertical thumbnail (1080x1920) for Shorts first frame ──────────────
    create_vertical_thumbnail(
        fruit_name, emoji, primary, accent, secondary,
        image_paths[0] if image_paths else None,
        vertical_path
    )

    # ── 2. Horizontal thumbnail (1280x720) for YouTube metadata ───────────────
    create_horizontal_thumbnail(
        fruit_name, emoji, primary, accent, secondary,
        image_paths[0] if image_paths else None,
        output_path
    )


def create_vertical_thumbnail(fruit_name, emoji, primary, accent, secondary,
                              bg_image_path, output_path):
    """1080x1920 — appears as first frame in Shorts feed"""
    W, H = 1080, 1920

    # Load fruit image as backdrop
    if bg_image_path and os.path.exists(bg_image_path):
        try:
            bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=3))
        except:
            bg = create_gradient(W, H, primary, secondary)
    else:
        bg = create_gradient(W, H, primary, secondary)

    # Dark overlay for text readability
    overlay = Image.new("RGBA", (W, H), (0,0,0,140))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── Top banner with channel name ──────────────────────────────────────────
    draw.rectangle([(0, 0), (W, 200)], fill=primary)
    draw.text((W//2, 70),  "🍎 FRUITS WITH FACTS",
              fill=(255,255,255), anchor="mm")
    draw.text((W//2, 145), "Educational Shorts",
              fill=(255,255,255,200), anchor="mm")

    # ── Big "5 FACTS" badge ───────────────────────────────────────────────────
    badge_y = 380
    # Glowing background circle
    for r in range(380, 320, -10):
        alpha_layer = Image.new("RGBA", (W, H), (0,0,0,0))
        ad = ImageDraw.Draw(alpha_layer)
        ad.ellipse([(W//2-r, badge_y-r), (W//2+r, badge_y+r)],
                   fill=(*accent, 30))
        img = Image.alpha_composite(img.convert("RGBA"), alpha_layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Solid badge circle
    draw.ellipse([(W//2-300, badge_y-300), (W//2+300, badge_y+300)],
                 fill=accent, outline=(0,0,0), width=8)

    # "5" - HUGE
    draw.text((W//2, badge_y - 60), "5", fill=(30,30,30), anchor="mm")
    # "FACTS"
    draw.text((W//2, badge_y + 130), "FACTS", fill=(30,30,30), anchor="mm")
    # "ABOUT"
    draw.text((W//2, badge_y + 230), "ABOUT", fill=(30,30,30), anchor="mm")

    # ── Fruit emoji row ───────────────────────────────────────────────────────
    draw.text((W//2, 850), emoji * 5, fill=(255,255,255), anchor="mm")

    # ── Big fruit name in colored bar ─────────────────────────────────────────
    bar_y = 1050
    bar_h = 200
    draw.rounded_rectangle(
        [(50, bar_y), (W-50, bar_y + bar_h)],
        radius=40, fill=primary, outline=accent, width=8
    )
    draw.text((W//2, bar_y + bar_h//2), fruit_name.upper(),
              fill=(255,255,255), anchor="mm")

    # ── Yellow attention banner ───────────────────────────────────────────────
    banner_y = 1320
    draw.rounded_rectangle(
        [(80, banner_y), (W-80, banner_y + 130)],
        radius=30, fill=accent
    )
    draw.text((W//2, banner_y + 65), "YOU WONT BELIEVE #3!",
              fill=secondary, anchor="mm")

    # ── Bottom decorative section ─────────────────────────────────────────────
    draw.text((W//2, 1550), "👇 WATCH NOW 👇",
              fill=accent, anchor="mm")
    draw.text((W//2, 1670), emoji * 7,
              fill=(255,255,255), anchor="mm")

    # ── Footer ────────────────────────────────────────────────────────────────
    draw.rectangle([(0, 1800), (W, H)], fill=primary)
    draw.text((W//2, 1860), "#Shorts #FruitFacts #DidYouKnow",
              fill=(255,255,255), anchor="mm")

    img.save(output_path, "PNG", quality=95)
    print(f"Vertical thumbnail saved: {output_path}")


def create_horizontal_thumbnail(fruit_name, emoji, primary, accent, secondary,
                                bg_image_path, output_path):
    """1280x720 — for YouTube metadata"""
    W, H = 1280, 720

    if bg_image_path and os.path.exists(bg_image_path):
        try:
            bg = Image.open(bg_image_path).resize((W, H), Image.LANCZOS)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
        except:
            bg = create_gradient(W, H, primary, secondary)
    else:
        bg = create_gradient(W, H, primary, secondary)

    overlay = Image.new("RGBA", (W, H), (0,0,0,130))
    img = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Left side — big "5"
    draw.ellipse([(40, 110), (540, 610)], fill=accent, outline=(0,0,0), width=6)
    draw.text((290, 290), "5", fill=(30,30,30), anchor="mm")
    draw.text((290, 480), "FACTS", fill=(30,30,30), anchor="mm")

    # Right side — fruit name
    draw.text((620, 180), "ABOUT", fill=(255,255,255), anchor="lm")
    draw.text((620, 300), fruit_name.upper(), fill=accent, anchor="lm")
    draw.text((620, 420), emoji * 4, fill=(255,255,255), anchor="lm")
    draw.text((620, 540), "YOU MUST KNOW!", fill=(255,255,255), anchor="lm")

    # Top banner
    draw.rectangle([(0, 0), (W, 60)], fill=primary)
    draw.text((W//2, 30), "🍎 FRUITS WITH FACTS",
              fill=(255,255,255), anchor="mm")

    # Bottom banner
    draw.rectangle([(0, 660), (W, H)], fill=primary)
    draw.text((W//2, 690), "#Shorts #FruitFacts #DidYouKnow",
              fill=(255,255,255), anchor="mm")

    img.save(output_path, "JPEG", quality=95)
    print(f"Horizontal thumbnail saved: {output_path}")


def create_gradient(width, height, color_top, color_bottom):
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for i in range(height):
        ratio = i / height
        r = int(color_top[0]*(1-ratio) + color_bottom[0]*ratio)
        g = int(color_top[1]*(1-ratio) + color_bottom[1]*ratio)
        b = int(color_top[2]*(1-ratio) + color_bottom[2]*ratio)
        draw.line([(0,i),(width,i)], fill=(r,g,b))
    return img


if __name__ == "__main__":
    data = load_video_data()
    fruit = data["fruit"]
    emoji = data.get("emoji", "🍎")
    colors = data.get("colors", {})
    prompts = data["image_prompts"]

    os.makedirs("output/images", exist_ok=True)

    image_paths = []
    for i, prompt in enumerate(prompts):
        out = f"output/images/scene_{i+1}.png"
        print(f"Generating image {i+1}/5...")
        generate_image(prompt, out, i, width=1080, height=1920)
        image_paths.append(out)
        time.sleep(5)

    # Create BOTH thumbnails
    print("\nCreating beautiful thumbnails...")
    create_beautiful_thumbnail(
        fruit, emoji, colors, image_paths,
        output_path="output/thumbnail.jpg",          # horizontal for YouTube
        vertical_path="output/thumbnail_vertical.png" # vertical for video
    )

    print(f"\nAll {len(image_paths)} images + 2 thumbnails ready!")
