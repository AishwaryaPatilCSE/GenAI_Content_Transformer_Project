# GenAI Platform for Automated Content Transformation

A simple Flask + OpenAI GenAI project implementing the required multimodal content-transformation workflow.

## Implemented requirements

1. Multimodal source input:
   - Text
   - PDF
   - DOCX
   - Images
   - Video upload
   - Prompt/context

2. Configurable generation:
   - Target audience
   - Tone
   - Language
   - Level of detail
   - Communication objective
   - Content style

3. Multiple outputs from the same source:
   - LinkedIn Post
   - Twitter/X Post or Thread
   - Advisory
   - Executive Summary
   - Infographic content + layout recommendations
   - Presentation + speaker notes
   - Video package: script, storyboard, narration, subtitles and visual recommendations

## Run in VS Code

### 1. Open this folder

Open the project folder in VS Code.

### 2. Create virtual environment

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:

```powershell
venv\Scripts\activate.bat
```

### 3. Install packages

```powershell
pip install -r requirements.txt
```

### 4. Configure API key

Copy `.env.example` to `.env`.

Put your API key in:

```text
OPENAI_API_KEY=your_key_here
```

Do not upload `.env` to GitHub.

### 5. Start

```powershell
python app.py
```

Open:

http://127.0.0.1:5000

## Important note about video

The dashboard accepts video files. This MVP does not automatically transcribe the video. For exact spoken content, paste a transcript into the source text box along with the video. This keeps the project simple and reliable for a college demo.

## GitHub

Do not commit:
- `.env`
- `venv/`
- `temp_uploads/`

Create a `.gitignore` containing:

```text
venv/
.env
temp_uploads/
__pycache__/
```
