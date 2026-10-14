# GenAI Platform for Automated Content Transformation — Gemini Free Version

A Flask-based SIH 2026 prototype for automated content transformation using the
Google Gemini API.

## AI backend

This version uses the **Google Gemini API** instead of OpenAI.

Default model:

```text
gemini-3.8-flash
```

Google currently provides a Free Tier for selected Gemini API models, subject to
the model's free-tier rate limits. See Google's official pricing page:
https://ai.google.dev/gemini-api/docs/pricing

## Implemented SIH requirements

### 1. Multimodal source input
- Text
- PDF
- DOCX
- Images
- Video
- Prompt/context

### 2. Configurable generation
- Target audience
- Tone
- Language
- Level of detail
- Communication objective
- Content style

### 3. Multiple outputs from the same source
- LinkedIn Post
- Twitter/X Post or Thread
- Advisory
- Executive Summary
- Infographic content + layout recommendations
- Presentation + speaker notes
- Video package: script, storyboard, narration, subtitles and visual recommendations

### 4. Innovation — Audience-Aware Personalization

The same source is deliberately adapted according to the selected audience's
knowledge level, needs and communication purpose.

Example:

```text
ONE SOURCE
     ↓
Audience-Aware Personalization
     ↓
Students | Executives | Developers | Public | Government
     ↓
Multiple Tailored Communication Outputs
```

This is implemented in the generation prompt so the selected audience affects
wording, terminology, depth, examples and communication approach.

## Run in VS Code

### 1. Open the project

Open this folder in VS Code.

### 2. Create the virtual environment

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
venv\Scripts\activate.bat
```

### 3. Install packages

```powershell
pip install -r requirements.txt
```

### 4. Get a Gemini API key

Create a key in Google AI Studio:

https://aistudio.google.com/apikey

Google AI Studio can create a Gemini API key for new users.

### 5. Create `.env`

Copy:

```text
.env.example
```

to:

```text
.env
```

Then put your key in:

```text
GEMINI_API_KEY=your_actual_key_here
```

Do not upload `.env` to GitHub.

### 6. Start the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

The terminal should stay running at:

```text
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

## Recommended first test

Use a short source such as:

```text
Cybersecurity awareness is important for every organization.
Employees should use strong passwords, enable multi-factor authentication,
avoid suspicious links, and report security incidents quickly.
```

Choose:

- Target Audience: Students
- Tone: Professional
- Language: English
- Detail: Medium
- Objective: Inform
- Style: Clear and professional
- Outputs: LinkedIn Post + Executive Summary + Presentation

Click **Transform & Verify**.

Then change the target audience to **Executives** and generate again.
The output should become more business-focused, demonstrating the
Audience-Aware Personalization feature.

## Video support

Gemini's Files API is used for uploaded videos. The application waits for the
video to finish processing before sending it to Gemini. Large/long videos may
take longer and may be subject to Gemini API limits.

## Important security

Never put your API key directly in `app.py`.

Do not commit:

```text
.env
venv/
temp_uploads/
__pycache__/
```

These are already included in `.gitignore`.

## SIH demo positioning

Use this architecture in your explanation:

```text
Multimodal Input
      ↓
Input Processing
      ↓
Content + Context Analysis
      ↓
Audience-Aware Personalization
      ↓
Gemini Generative AI
      ↓
Multi-Format Output Generator
      ↓
LinkedIn | X | Advisory | Summary | Infographic
Presentation | Video Package
```
