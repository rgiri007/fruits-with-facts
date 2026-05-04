"""
Step 1: Generate YouTube Shorts script using Google Gemini
With automatic retry + model fallback to handle high demand errors
"""

import json
import os
import sys
import time
import random
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
    print(f"Next fruit: {remaining[0]}")
    return remaining[0]


# ── Build prompt ─────────────────────────────────────────────────────────────
def build_prompt(fruit_name):
    return f"""You are a YouTube Shorts script writer for "Fruits with Facts" channel.

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
  "image_prompts": [
    "Detailed image prompt for fresh {fruit_name} on white background, food photography",
    "Detailed image prompt for {fruit_name} cut open showing inside, macro photography",
    "Detailed image prompt for {fruit_name} growing on tree or plant in nature",
    "Detailed image prompt for {fruit_name} with water droplets, dark moody background",
    "Detailed image prompt for {fruit_name} in rustic bowl or basket, warm lighting"
  ],
  "colors": {{
    "primary": "Pick one vibrant hex color matching {fruit_name} color e.g. #FF6B35",
    "secondary": "Pick a complementary darker hex color",
    "accent": "Pick a bright accent hex color for text highlights"
  }},
  "emoji": "Pick the best single emoji for {fruit_name}"
}}

Write REAL facts. All voiceover fields must contain actual sentences, not instructions."""


# ── Try Gemini with automatic retry + model fallback ─────────────────────────
def call_gemini(prompt, api_key):
    """
    Try multiple models in order of preference.
    Each model gets retried with exponential backoff.
    """
    # Models ordered from best/most-popular (highest demand) to lighter alternatives
    models = [
        "gemini-2.5-flash",        # Best quality, sometimes overloaded
        "gemini-2.5-flash-lite",   # Lighter, less crowded
        "gemini-2.0-flash",        # Older but stable
        "gemini-2.0-flash-lite",   # Lightest fallback
    ]

    last_error = None

    for model in models:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 2000,
                "topP": 0.95
            }
        }

        # Retry each model up to 4 times with exponential backoff
        for attempt in range(4):
            try:
                print(f"Trying {model} (attempt {attempt+1}/4)...")
                response = requests.post(url, json=payload, timeout=60)

                if response.status_code == 200:
                    print(f"Success with {model}!")
                    return response.json()

                error_text = response.text.lower()

                # 503 = overloaded, 429 = rate limit — retry with backoff
                if response.status_code in [429, 503] or "high demand" in error_text or "overloaded" in error_text:
                    wait = (2 ** attempt) + random.uniform(0, 2)  # 1-3s, 2-4s, 4-6s, 8-10s
                    print(f"Model busy ({response.status_code}). Waiting {wait:.1f}s...")
                    time.sleep(wait)
                    last_error = response.text
                    continue

                # 404 = model not available, skip to next model
                if response.status_code == 404:
                    print(f"Model {model} not available, trying next...")
                    last_error = response.text
                    break

                # Other errors — also try next model
                print(f"Error {response.status_code}, trying next model...")
                last_error = response.text
                break

            except requests.exceptions.Timeout:
                print(f"Timeout, retrying...")
                time.sleep(5)
                last_error = "timeout"
                continue
            except Exception as e:
                print(f"Network error: {e}")
                last_error = str(e)
                time.sleep(3)
                continue

    raise Exception(
        f"All Gemini models failed. Last error: {last_error}\n"
        "Try again in a few minutes — Gemini is experiencing high demand."
    )


# ── Parse JSON safely from Gemini response ───────────────────────────────────
def parse_response(result):
    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # Clean markdown wrapping
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            cleaned = part.strip().lstrip("json").strip()
            if cleaned.startswith("{"):
                raw = cleaned
                break

    # Find JSON boundaries
    start, end = raw.find("{"), raw.rfind("}") + 1
    if start != -1 and end > start:
        raw = raw[start:end]

    return json.loads(raw)


# ── Main script generation ───────────────────────────────────────────────────
def generate_script(fruit_name):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in GitHub Secrets!")

    prompt = build_prompt(fruit_name)
    result = call_gemini(prompt, api_key)
    data = parse_response(result)

    # Validation
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


if __name__ == "__main__":
    fruit = get_next_fruit()
    data = generate_script(fruit)
    save_output(data)
