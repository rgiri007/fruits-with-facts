"""
Step 3: Generate fruit images using Pollinations AI
100% FREE - No account - No watermark
Images optimized for 9:16 vertical Shorts format
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
    """Pollinations AI — free, no account, no watermark, vertical format"""
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
            print(f"  Requesting image {index+1} (attempt {attempt+1})...")
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 1000:
                img = Image.open(io.BytesIO(r.content))
                img = img.resize((1080, 1920), Image.LANCZOS)
                img.save(output_path, "PNG", quality=95)
                print(f"  Saved: {output_path}")
                return True
            time.sleep(10)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(10)

    return create_fallback_image(output_path, index)


def create_fallback_image(output_path, index):
    """Vibrant gradient fallback — still looks great"""
    gradients = [
        [(255,107,53),(255,180,50)],   # Orange-Yellow
        [(50,205,50),(0,168,107)],      # Green
        [(255,20,147),(255,105,180)],   # Pink
        [(100,149,237),(65,105,225)],   # Blue
        [(255,215,0),(255,140,0)],      # Gold-Orange
    ]
    c = gradients[index % len(gradients)]
    img = Image.new("RGB", (1080, 1920))
    draw = ImageDraw.Draw(img)
    for i in range(1920):
        ratio = i / 1920
        r = int(c[0][0]*(1-ratio) + c[1][0]*ratio)
        g = int(c[0][1]*(1-ratio) + c[1][1]*ratio)
        b = int(c[0][2]*(1-ratio) + c[1][2]*ratio)
        draw.line([(0,i),(1080,i)], fill=(r,g,b))
    img.save(output_path, "PNG")
    print(f"  Fallback gradient saved: {output_path}")
    return True


def create_thumbnail(fruit_name, emoji, colors, first_image_path, output_path):
    """Vibrant vertical thumbnail for Shorts"""
    try:
        img = Image.open(first_image_path).resize((1080, 1920), Image.LANCZOS)
    except Exception:
        img = Image.new("RGB", (1080, 1920), (255, 107, 53))

    # Strong gradient overlay at top and bottom
    overlay = Image.new("RGBA", (1080, 1920), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    # Top dark band for title
    draw.rectangle([(0,0),(1080,400)], fill=(0,0,0,180))
    # Bottom dark band for channel name
    draw.rectangle([(0,1550),(1080,1920)], fill=(0,0,0,160))

    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    def outlined_text(draw, pos, text, size=80, fill=(255,255,255), outline=(0,0,0)):
        x, y = pos
        for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3),(-4,0),(4,0),(0,-4),(0,4)]:
            draw.text((x+dx, y+dy), text, fill=outline)
        draw.text((x, y), text, fill=fill)

    outlined_text(draw, (80, 60),  "5 FACTS ABOUT",     fill=(255,220,50))
    outlined_text(draw, (80, 160), fruit_name.upper(),   fill=(255,255,255))
    outlined_text(draw, (80, 280), emoji * 3,            fill=(255,255,255))
    outlined_text(draw, (80, 1600), "Fruits with Facts", fill=(200,200,200))
    outlined_text(draw, (80, 1700), "#Shorts",           fill=(100,200,255))

    img.save(output_path, "JPEG", quality=95)
    print(f"Thumbnail saved: {output_path}")


if __name__ == "__main__":
    data = load_video_data()
    fruit = data["fruit"]
    emoji = data.get("emoji", "🍎")
    colors = data.get("colors", {})
    prompts = data["image_prompts"]

    os.makedirs("output/images", exist_ok=True)

    # Generate vertical 9:16 images
    image_paths = []
    for i, prompt in enumerate(prompts):
        out = f"output/images/scene_{i+1}.png"
        print(f"Generating image {i+1}/5...")
        generate_image(prompt, out, i, width=1080, height=1920)
        image_paths.append(out)
        time.sleep(5)

    # Create thumbnail
    create_thumbnail(fruit, emoji, colors, image_paths[0], "output/thumbnail.jpg")
    print(f"\nAll {len(image_paths)} images ready!")
