"""
Step 3: Generate fruit images using Pollinations AI
100% FREE - No account needed - No API key - No watermark
Simply calls a free public URL API
"""

import json
import os
import time
import requests
from PIL import Image
import io
import urllib.parse

# ── Load video data ───────────────────────────────────────────────────────────

def load_video_data():
with open("output/video_data.json", "r") as f:
return json.load(f)

# ── Generate image using Pollinations AI ─────────────────────────────────────

def generate_image(prompt, output_path, index):
"""
Pollinations AI - completely free, no account, no API key, no watermark
Just a simple URL call!
"""
enhanced_prompt = (
f"{prompt}, ultra realistic, 4k, high quality, "
"sharp focus, professional photography, vibrant colors"
)

```
negative = "watermark, text, logo, blurry, low quality, cartoon, drawing"

encoded_prompt = urllib.parse.quote(enhanced_prompt)

# Pollinations free API - no key needed!
url = (
    f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    f"?width=1920&height=1080&seed={index * 42}&nologo=true&enhance=true"
)

print(f"  Requesting image from Pollinations AI...")

for attempt in range(3):
    try:
        response = requests.get(url, timeout=120)

        if response.status_code == 200 and len(response.content) > 1000:
            image = Image.open(io.BytesIO(response.content))
            image = image.resize((1920, 1080), Image.LANCZOS)
            image.save(output_path, "PNG", quality=95)
            print(f"  Image saved: {output_path}")
            return True
        else:
            print(f"  Attempt {attempt+1} failed, retrying...")
            time.sleep(10)

    except Exception as e:
        print(f"  Error on attempt {attempt+1}: {e}")
        time.sleep(10)

# Fallback: create gradient image with PIL
return create_fallback_image(output_path, index)
```

# ── Fallback gradient image ───────────────────────────────────────────────────

def create_fallback_image(output_path, index):
from PIL import Image, ImageDraw

```
color_pairs = [
    [(255, 140, 0), (255, 69, 0)],
    [(50, 205, 50), (0, 100, 0)],
    [(255, 20, 147), (139, 0, 90)],
    [(30, 144, 255), (0, 0, 139)],
    [(255, 215, 0), (184, 134, 11)],
]
c = color_pairs[index % len(color_pairs)]
img = Image.new("RGB", (1920, 1080))
draw = ImageDraw.Draw(img)
for i in range(1080):
    r = int(c[0][0] + (c[1][0] - c[0][0]) * i / 1080)
    g = int(c[0][1] + (c[1][1] - c[0][1]) * i / 1080)
    b = int(c[0][2] + (c[1][2] - c[0][2]) * i / 1080)
    draw.line([(0, i), (1920, i)], fill=(r, g, b))
img.save(output_path, "PNG")
print(f"  Fallback image saved: {output_path}")
return True
```

# ── Create YouTube thumbnail ──────────────────────────────────────────────────

def create_thumbnail(fruit_name, first_image_path, output_path):
from PIL import Image, ImageDraw

```
try:
    img = Image.open(first_image_path).resize((1280, 720), Image.LANCZOS)
except Exception:
    img = Image.new("RGB", (1280, 720), (255, 140, 0))

# Dark overlay at bottom for text
overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)
draw.rectangle([(0, 380), (1280, 720)], fill=(0, 0, 0, 160))
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

draw = ImageDraw.Draw(img)

def draw_outlined_text(draw, pos, text, fill, outline=(0, 0, 0)):
    x, y = pos
    for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3),(-3,0),(3,0),(0,-3),(0,3)]:
        draw.text((x+dx, y+dy), text, fill=outline)
    draw.text((x, y), text, fill=fill)

draw_outlined_text(draw, (70, 420), "5 FACTS ABOUT", fill=(255, 220, 0))
draw_outlined_text(draw, (70, 520), fruit_name.upper(), fill=(255, 255, 255))

img.save(output_path, "JPEG", quality=95)
print(f"Thumbnail saved: {output_path}")
```

# ── Main ──────────────────────────────────────────────────────────────────────

if **name** == "**main**":
data = load_video_data()
fruit_name = data["fruit"]
image_prompts = data["image_prompts"]

```
os.makedirs("output/images", exist_ok=True)

image_paths = []
for i, prompt in enumerate(image_prompts):
    out_path = f"output/images/scene_{i+1}.png"
    print(f"Generating image {i+1}/5...")
    generate_image(prompt, out_path, i)
    image_paths.append(out_path)
    time.sleep(5)  # Be polite to free API

create_thumbnail(fruit_name, image_paths[0], "output/thumbnail.jpg")
print(f"\nAll {len(image_paths)} images generated!")
```
