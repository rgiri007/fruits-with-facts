“””
Step 1: Generate YouTube script, title, description, and tags
Uses Google Gemini API - 100% FREE, no credit card required
Free tier: 1,500 requests/day (more than enough)
Get your free key at: aistudio.google.com
“””

import json
import os
import sys
import requests

# ── Load fruit list and find next fruit ──────────────────────────────────────

def get_next_fruit():
with open(“fruits_list.txt”, “r”) as f:
all_fruits = [line.strip() for line in f if line.strip()
and not line.startswith(”#”)]

```
done_fruits = []
if os.path.exists("fruits_done.txt"):
    with open("fruits_done.txt", "r") as f:
        done_fruits = [line.strip() for line in f if line.strip()
                       and not line.startswith("#")]

remaining = [f for f in all_fruits if f not in done_fruits]

if not remaining:
    print("All fruits completed! Add more to fruits_list.txt")
    sys.exit(0)

next_fruit = remaining[0]
print(f"Next fruit: {next_fruit}")
return next_fruit
```

# ── Generate script using Gemini API ─────────────────────────────────────────

def generate_script(fruit_name):
api_key = os.environ.get(“GEMINI_API_KEY”)
if not api_key:
raise ValueError(“GEMINI_API_KEY not set in GitHub Secrets!”)

```
prompt = f"""You are a script writer for a faceless YouTube channel called Fruits with Facts.
```

Create a complete video package for a fruit called: {fruit_name}

Return ONLY a valid JSON object with these exact keys, no markdown, no backticks, no extra text:
{{
“fruit”: “{fruit_name}”,
“title”: “5 Amazing Facts About {fruit_name} You Never Knew!”,
“description”: “Discover 5 incredible facts about {fruit_name}! From health benefits to history. Subscribe to Fruits with Facts for weekly fruit knowledge! #{fruit_name} #fruits #facts #healthyfood #didyouknow”,
“tags”: [”{fruit_name}”, “fruit facts”, “healthy food”, “did you know”, “food facts”, “nutrition”, “fruits”, “amazing facts”, “educational”, “short facts”],
“voiceover”: {{
“intro”: “Welcome to Fruits with Facts! Today we are exploring the amazing {fruit_name}. Stay tuned for 5 incredible facts you probably never knew!”,
“fact_1”: “Fact number one. Write 2 to 3 sentences about a surprising fact about {fruit_name}.”,
“fact_2”: “Fact number two. Write 2 to 3 sentences about a health benefit of {fruit_name}.”,
“fact_3”: “Fact number three. Write 2 to 3 sentences about the origin or history of {fruit_name}.”,
“fact_4”: “Fact number four. Write 2 to 3 sentences about how {fruit_name} grows.”,
“fact_5”: “Fact number five. Write 2 to 3 sentences about a unique use or world record related to {fruit_name}.”,
“outro”: “Those were 5 amazing facts about {fruit_name}! Please like and subscribe to Fruits with Facts for more fruity knowledge every week. See you in the next video!”
}},
“image_prompts”: [
“Professional food photography of fresh {fruit_name} on clean white background, vibrant colors, ultra realistic, 4k”,
“Close up macro photo of {fruit_name} cut in half showing inside flesh, natural lighting, high detail”,
“{fruit_name} growing naturally on tree in tropical environment, green leaves, sunshine”,
“Fresh {fruit_name} with water droplets sparkling, dark background, studio lighting”,
“Beautiful arrangement of {fruit_name} fruits in a wooden bowl, warm lighting, rustic style”
]
}}

Write real accurate interesting facts. Make voiceover sound natural and enthusiastic.”””

```
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
}

response = requests.post(url, json=payload, timeout=60)

if response.status_code != 200:
    raise Exception(f"Gemini API error {response.status_code}: {response.text}")

result = response.json()
raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

# Clean if wrapped in markdown code blocks
if "```" in raw:
    parts = raw.split("```")
    for part in parts:
        part = part.strip()
        if part.startswith("json"):
            part = part[4:].strip()
        if part.startswith("{"):
            raw = part
            break

data = json.loads(raw.strip())
print(f"Script generated for: {fruit_name}")
return data
```

# ── Save output ───────────────────────────────────────────────────────────────

def save_output(data):
os.makedirs(“output”, exist_ok=True)
with open(“output/video_data.json”, “w”) as f:
json.dump(data, f, indent=2)
print(“Saved to output/video_data.json”)

# ── Main ──────────────────────────────────────────────────────────────────────

if **name** == “**main**”:
fruit = get_next_fruit()
data = generate_script(fruit)
save_output(data)
print(f”Title: {data[‘title’]}”)
print(f”Tags: {’, ’.join(data[‘tags’][:5])}…”)