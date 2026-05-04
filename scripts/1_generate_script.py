"""
Step 1: Generate SHORT script for YouTube Shorts (max 60 seconds)
Uses Google Gemini API - FREE, no credit card
"""

import json
import os
import sys
import requests


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
        print("All fruits completed!")
        sys.exit(0)
    next_fruit = remaining[0]
    print(f"Next fruit: {next_fruit}")
    return next_fruit


def generate_script(fruit_name):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in GitHub Secrets!")

    prompt = f"""You are a YouTube Shorts script writer for "Fruits with Facts" channel.

Create a punchy 60-second script about: {fruit_name}

STRICT RULES:
- Total spoken words must be 120-140 words MAX (fits in 60 seconds)
- Each fact must be ONE punchy sentence only
- No filler words, no long intros
- Enthusiastic and fast-paced tone

Return ONLY raw valid JSON, no markdown, no backticks:

{{
  "fruit": "{fruit_name}",
  "title": "5 Wild Facts About {fruit_name} #Shorts #FruitFacts",
  "description": "Write 80-100 words about {fruit_name} facts. Include health benefits teaser, fun history, and call to action. End with hashtags: #{fruit_name} #FruitsWithFacts #FruitFacts #Shorts #DidYouKnow #HealthyFood #NutritionFacts #FoodFacts",
  "tags": ["{fruit_name}", "fruit facts", "shorts", "did you know", "healthy food", "nutrition facts", "food facts", "fruits with facts", "5 facts", "educational shorts"],
  "voiceover": {{
    "hook": "Write ONE punchy hook sentence to grab attention instantly about {fruit_name} - max 12 words",
    "fact_1": "Write ONE surprising fact sentence about {fruit_name} - max 20 words",
    "fact_2": "Write ONE health benefit sentence about {fruit_name} - max 20 words",
    "fact_3": "Write ONE history or origin sentence about {fruit_name} - max 20 words",
    "fact_4": "Write ONE weird or funny fact sentence about {fruit_name} - max 20 words",
    "fact_5": "Write ONE record or unique use sentence about {fruit_name} - max 20 words",
    "outro": "Follow for more fruity facts! Like and subscribe to Fruits with Facts!"
  }},
  "colors": {{
    "primary": "Pick one vibrant hex color matching {fruit_name} color e.g. #FF6B35 for orange",
    "secondary": "Pick a complementary darker hex color",
    "accent": "Pick a bright accent hex color for text highlights"
  }},
  "emoji": "Pick the best single emoji for {fruit_name}"
}}

Write REAL facts. All voiceover fields must contain actual sentences, not instructions."""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-2.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2000}
    }

    print("Calling Gemini API...")
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code != 200:
        raise Exception(f"Gemini error {response.status_code}: {response.text}")

    result = response.json()
    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            cleaned = part.strip().lstrip("json").strip()
            if cleaned.startswith("{"):
                raw = cleaned
                break

    start, end = raw.find("{"), raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    data = json.loads(raw)
    assert len(data.get("description", "")) > 50, "Description too short"
    assert len(data.get("voiceover", {}).get("fact_1", "")) > 10, "Fact 1 missing"

    print(f"Script generated for: {fruit_name}")
    return data


def save_output(data):
    os.makedirs("output", exist_ok=True)
    with open("output/video_data.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Title: {data.get('title')}")
    print(f"Hook: {data.get('voiceover', {}).get('hook')}")
    print(f"Colors: {data.get('colors')}")


if __name__ == "__main__":
    fruit = get_next_fruit()
    data = generate_script(fruit)
    save_output(data)
