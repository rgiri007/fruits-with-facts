"""
Step 1: Generate YouTube script, title, description, and tags
Uses Google Gemini API - 100% FREE, no credit card required
Free tier: 1,500 requests/day
Get your free key at: aistudio.google.com
"""

import json
import os
import sys
import requests


# ── Load fruit list and find next fruit ──────────────────────────────────────
def get_next_fruit():
    with open("fruits_list.txt", "r") as f:
        all_fruits = [line.strip() for line in f if line.strip()
                      and not line.startswith("#")]

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


# ── Generate script using Gemini API ─────────────────────────────────────────
def generate_script(fruit_name):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in GitHub Secrets!")

    # NOTE: We ask Gemini to fill in ALL values — no placeholder text
    prompt = f"""You are a YouTube content creator for a faceless educational channel called "Fruits with Facts".

Your task: Create a COMPLETE video package for the fruit: {fruit_name}

Return ONLY raw valid JSON. No markdown. No backticks. No explanation. Just the JSON object.

The JSON must have exactly these fields filled with REAL content (not placeholder text):

{{
  "fruit": "{fruit_name}",

  "title": "Write a catchy YouTube title max 60 characters including the words 5 Facts and {fruit_name}",

  "description": "Write a full 150 to 200 word YouTube video description about {fruit_name}. Include what the video covers, 3 to 4 interesting teaser facts, a call to action to like and subscribe, and relevant keywords naturally woven in. End with a line of relevant hashtags like #FruitFacts #{fruit_name} #HealthyFood #DidYouKnow #FruitsWithFacts #NutritionFacts #FoodFacts",

  "tags": ["write", "10", "to", "15", "real", "relevant", "YouTube", "tags", "as", "strings", "for", "a", "video", "about", "{fruit_name}"],

  "voiceover": {{
    "intro": "Write a warm 2 sentence intro welcoming viewers and introducing {fruit_name} as todays topic",
    "fact_1": "Write 2 to 3 sentences sharing a genuinely surprising or little known fact about {fruit_name}",
    "fact_2": "Write 2 to 3 sentences about the most impressive health benefit or nutritional value of {fruit_name}",
    "fact_3": "Write 2 to 3 sentences about the historical origin or cultural significance of {fruit_name}",
    "fact_4": "Write 2 to 3 sentences about how {fruit_name} grows or an interesting agricultural fact about it",
    "fact_5": "Write 2 to 3 sentences about a unique world record, unusual use, or fun culinary fact about {fruit_name}",
    "outro": "Write a friendly 2 sentence outro thanking viewers and asking them to like and subscribe to Fruits with Facts"
  }},

  "image_prompts": [
    "Write a detailed image generation prompt for: fresh {fruit_name} on white background, food photography style",
    "Write a detailed image generation prompt for: {fruit_name} cut open showing inside, macro photography",
    "Write a detailed image generation prompt for: {fruit_name} growing on a tree or plant in nature",
    "Write a detailed image generation prompt for: {fruit_name} with water droplets, dark moody background",
    "Write a detailed image generation prompt for: {fruit_name} in a rustic bowl or basket, warm lighting"
  ]
}}

IMPORTANT RULES:
- Every field must contain REAL written content, not instructions or placeholder text
- The description must be 150-200 words of real sentences, ending with real hashtags
- Tags must be real relevant search terms people would use on YouTube
- Voiceover must contain real facts about {fruit_name}, not template instructions
- All facts must be accurate and verifiable
- Tone should be enthusiastic, educational, and friendly"""

    url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-pro:generateContent?key={api_key}"
)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2500,
            "topP": 0.95
        }
    }

    print("Calling Gemini API...")
    response = requests.post(url, json=payload, timeout=60)

    if response.status_code != 200:
        raise Exception(f"Gemini API error {response.status_code}: {response.text}")

    result = response.json()
    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Aggressively clean any markdown wrapping
    if "```" in raw:
        # Extract content between first ``` and last ```
        parts = raw.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("{") and cleaned.endswith("}"):
                raw = cleaned
                break

    raw = raw.strip()

    # Final safety: find the first { and last } 
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    data = json.loads(raw)

    # Validate key fields are not empty or placeholder-like
    assert len(data.get("description", "")) > 100, "Description too short — Gemini may have returned placeholder text"
    assert len(data.get("tags", [])) >= 5,         "Not enough tags returned"
    assert len(data.get("voiceover", {}).get("fact_1", "")) > 50, "fact_1 voiceover too short"

    print(f"Script generated successfully for: {fruit_name}")
    return data


# ── Save output ───────────────────────────────────────────────────────────────
def save_output(data):
    os.makedirs("output", exist_ok=True)
    with open("output/video_data.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved: output/video_data.json")

    # Print preview so we can verify in GitHub Actions logs
    print("\n--- PREVIEW ---")
    print(f"Title      : {data.get('title', 'MISSING')}")
    print(f"Description: {data.get('description', 'MISSING')[:120]}...")
    print(f"Tags       : {data.get('tags', [])}")
    print(f"Fact 1     : {data.get('voiceover', {}).get('fact_1', 'MISSING')[:80]}...")
    print("---------------\n")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fruit = get_next_fruit()
    data  = generate_script(fruit)
    save_output(data)
