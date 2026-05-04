# 🍎 Fruits with Facts — Full Automation Setup Guide

> **Fully automated YouTube channel. Zero human involvement after setup.**
> Runs 3 videos/week automatically. 100% free. No watermarks.

-----

## ⏱️ Setup Time: ~60 minutes (one-time only)

-----

## 📋 PHASE 1: Create Your GitHub Repository (10 min)

### Step 1.1 — Create GitHub Account

1. Go to **github.com**
1. Click **Sign Up**
1. Create your free account

### Step 1.2 — Create New Repository

1. Click the **+** icon (top right) → **New repository**
1. Repository name: `fruits-with-facts`
1. Set to **Private** (to protect your API keys)
1. Click **Create repository**

### Step 1.3 — Upload All Files

For each file listed below, click **Add file → Create new file**:

|File Path                             |Content                |
|--------------------------------------|-----------------------|
|`.github/workflows/generate_video.yml`|Copy from provided file|
|`scripts/1_generate_script.py`        |Copy from provided file|
|`scripts/2_generate_voice.py`         |Copy from provided file|
|`scripts/3_generate_images.py`        |Copy from provided file|
|`scripts/4_assemble_video.py`         |Copy from provided file|
|`scripts/5_upload_youtube.py`         |Copy from provided file|
|`requirements.txt`                    |Copy from provided file|
|`fruits_list.txt`                     |Copy from provided file|
|`fruits_done.txt`                     |Leave empty            |

-----

## 📋 PHASE 2: Get Your Free API Keys (20 min)

### Step 2.1 — Anthropic API Key (For Script Writing)

1. Go to **console.anthropic.com**
1. Sign up for free account
1. Click **API Keys** → **Create Key**
1. Copy the key (starts with `sk-ant-...`)
1. ⚠️ Free tier gives $5 credit (~500 videos worth)

### Step 2.2 — Hugging Face API Key (For Voice + Images)

1. Go to **huggingface.co**
1. Sign up for free account
1. Click your avatar → **Settings → Access Tokens**
1. Click **New token** → Name it `fruits-bot` → Role: **Read**
1. Copy the token (starts with `hf_...`)
1. ⚠️ Free tier: 1000 requests/day — enough for 3 videos/week

-----

## 📋 PHASE 3: YouTube API Setup (20 min)

> This is the most complex step. Follow carefully.

### Step 3.1 — Create Google Cloud Project

1. Go to **console.cloud.google.com**
1. Click **Select a project** → **New Project**
1. Name: `FruitsWithFacts` → Click **Create**
1. Make sure this project is selected

### Step 3.2 — Enable YouTube Data API

1. Go to **APIs & Services → Library**
1. Search for **YouTube Data API v3**
1. Click it → Click **Enable**

### Step 3.3 — Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
1. Click **+ Create Credentials → OAuth client ID**
1. If asked to configure consent screen:
- Click **Configure Consent Screen**
- Choose **External** → Click **Create**
- App name: `Fruits With Facts Bot`
- Your email for support
- Click **Save and Continue** (skip all optional fields)
- On **Scopes** page → Click **Save and Continue**
- On **Test Users** → Add your Gmail → **Save and Continue**
- Click **Back to Dashboard**
1. Back at Credentials → **+ Create Credentials → OAuth client ID**
1. Application type: **Desktop app**
1. Name: `FruitsBot`
1. Click **Create**
1. **Download the JSON file** (click the download icon)
1. Save your **Client ID** and **Client Secret** from the popup

### Step 3.4 — Get Your Refresh Token

1. Go to this URL (replace YOUR_CLIENT_ID with yours):

```
https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code&scope=https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube&access_type=offline&prompt=consent
```

1. Login with your YouTube channel Google account
1. Click **Allow**
1. Copy the **authorization code** shown on screen
1. Now exchange it for a refresh token. Go to this website: **reqbin.com/curl**
1. Paste this (replace the values):

```
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=PASTE_AUTH_CODE_HERE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob" \
  -d "grant_type=authorization_code"
```

1. Click **Run**
1. Copy the **refresh_token** value from the response

-----

## 📋 PHASE 4: Add Secrets to GitHub (5 min)

1. Go to your GitHub repository
1. Click **Settings → Secrets and variables → Actions**
1. Click **New repository secret** for each:

|Secret Name            |Value                |
|-----------------------|---------------------|
|`ANTHROPIC_API_KEY`    |Your `sk-ant-...` key|
|`HUGGINGFACE_API_KEY`  |Your `hf_...` token  |
|`YOUTUBE_CLIENT_ID`    |From Google Cloud    |
|`YOUTUBE_CLIENT_SECRET`|From Google Cloud    |
|`YOUTUBE_REFRESH_TOKEN`|From Step 3.4        |

-----

## 📋 PHASE 5: Test Your Pipeline (5 min)

### Run it manually to test:

1. In your GitHub repo, click **Actions** tab
1. Click **Generate & Upload Fruits Video**
1. Click **Run workflow → Run workflow**
1. Watch the logs in real-time
1. ✅ If all 5 steps show green checkmarks — you’re done!

### Check your YouTube channel:

- The first video should appear within minutes of the workflow completing
- Title will be something like: “5 Amazing Facts About Apple 🍎”

-----

## 📅 Automatic Schedule

Once setup is complete, videos post automatically:

|Day      |Time       |Action                        |
|---------|-----------|------------------------------|
|Monday   |9:00 AM UTC|Auto-generates + uploads video|
|Wednesday|9:00 AM UTC|Auto-generates + uploads video|
|Friday   |9:00 AM UTC|Auto-generates + uploads video|

**That’s 3 videos/week = 12 videos/month = 144 videos/year!**

The system will automatically go through all 100 fruits in `fruits_list.txt`.
At 3/week, that’s **33 weeks of content** without any intervention.

-----

## 🔧 Customization Options

### Change posting frequency:

Edit `.github/workflows/generate_video.yml` line:

```yaml
- cron: '0 9 * * 1,3,5'   # Mon, Wed, Fri
# Change to daily:
- cron: '0 9 * * *'        # Every day
# Change to weekly:
- cron: '0 9 * * 1'        # Every Monday only
```

### Change video voice:

Edit `scripts/2_generate_voice.py`:

```python
"voice": "af_sarah"    # Female voice
"voice": "af_bella"    # Different female voice
"voice": "am_adam"     # Male voice
```

### Add more fruits:

Just add more lines to `fruits_list.txt` in GitHub

### Change upload privacy:

Edit `scripts/5_upload_youtube.py`:

```python
"privacyStatus": "public"    # Immediate public
"privacyStatus": "unlisted"  # Only with link
"privacyStatus": "private"   # Only you
```

-----

## 🆘 Troubleshooting

### ❌ “ANTHROPIC_API_KEY not set”

→ Double-check you added it in GitHub Secrets (Phase 4)

### ❌ “Upload init failed: 401”

→ Your YouTube refresh token expired. Repeat Step 3.4

### ❌ “Model loading” timeout on Hugging Face

→ Free tier models sleep. The script retries 3 times automatically.
If still failing, re-run the workflow manually.

### ❌ FFmpeg video assembly error

→ Check if all 5 images were generated in `output/images/`
The script has fallback image generation built in.

### ❌ All fruits done

→ Add more fruits to `fruits_list.txt`

-----

## 💰 Cost Summary

|Service       |Free Tier        |Cost After    |
|--------------|-----------------|--------------|
|GitHub Actions|2,000 min/month  |$0 for our use|
|Anthropic API |$5 credit        |~$0.003/video |
|Hugging Face  |1,000 req/day    |Always free   |
|YouTube API   |Unlimited uploads|Always free   |
|**TOTAL**     |**$0**           |**< $1/month**|

-----

## 🎉 You’re Done!

Your channel will now automatically:

1. ✅ Pick the next fruit from your list
1. ✅ Write an engaging 5-facts script
1. ✅ Generate natural voiceover audio
1. ✅ Create 5 AI-generated fruit images
1. ✅ Assemble into a complete MP4 with captions
1. ✅ Upload to YouTube with title, description & thumbnail

**All while you sleep. 3x per week. Forever. 🚀**
