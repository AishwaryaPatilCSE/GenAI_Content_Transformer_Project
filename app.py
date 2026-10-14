import os, base64, mimetypes, json
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

ALLOWED = {
    "txt","md","pdf","docx","png","jpg","jpeg","webp","mp4","mov","avi","mkv",
    "webm","m4v"
}

OUTPUTS = {
    "linkedin": "Professional LinkedIn post",
    "twitter": "Twitter/X post or thread",
    "advisory": "Structured advisory document",
    "summary": "Concise executive summary",
    "infographic": "Infographic content with title, sections, key statistics/messages and visual/layout recommendations",
    "presentation": "Presentation with slide titles, slide content and speaker notes",
    "video": "Complete video package containing title, objective, script, scene-by-scene storyboard, narration, subtitles/captions and visual recommendations"
}

def get_client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in the .env file.")
    return OpenAI(api_key=key)

def file_to_text(path):
    ext = path.suffix.lower()
    if ext in [".txt", ".md"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            return f"[PDF extraction failed: {e}]"

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"[DOCX extraction failed: {e}]"

    return ""

def make_image_data(path):
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{data}"

def build_prompt(source, audience, tone, language, detail, objective, style, selected):
    output_instructions = "\n".join(
        f"{i}. {OUTPUTS[k]}" for i, k in enumerate(selected, 1)
    )
    return f"""
You are the GenAI engine of an automated content transformation platform.

SOURCE CONTENT:
{source}

CONFIGURATION:
Target audience: {audience}
Tone: {tone}
Language: {language}
Level of detail: {detail}
Communication objective: {objective}
Content style: {style}

SELECTED OUTPUTS:
{output_instructions}

TASK:
Transform the same source content into EVERY selected deliverable.
Do not invent facts. Preserve important names, numbers, dates and claims from the source.
If information is missing, clearly label assumptions instead of fabricating facts.
Return clean Markdown with a separate heading for every selected output.
Make each output ready to copy/use.
"""

@app.route("/")
def index():
    return render_template("index.html")

@app.post("/api/transform")
def transform():
    try:
        client = get_client()
        audience = request.form.get("audience", "General")
        tone = request.form.get("tone", "Professional")
        language = request.form.get("language", "English")
        detail = request.form.get("detail", "Medium")
        objective = request.form.get("objective", "Inform")
        style = request.form.get("style", "Clear and professional")
        selected = request.form.getlist("outputs")
        prompt = request.form.get("source_text", "").strip()

        if not selected:
            return jsonify(error="Select at least one output format."), 400
        if not prompt and "file" not in request.files:
            return jsonify(error="Enter source text or upload a file."), 400

        source_parts = []
        if prompt:
            source_parts.append("USER-PROVIDED TEXT:\n" + prompt)

        uploaded = request.files.get("file")
        image_part = None
        if uploaded and uploaded.filename:
            ext = Path(uploaded.filename).suffix.lower().lstrip(".")
            if ext not in ALLOWED:
                return jsonify(error=f"Unsupported file type: .{ext}"), 400

            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            safe_name = Path(uploaded.filename).name
            path = temp_dir / safe_name
            uploaded.save(path)

            if ext in ["png","jpg","jpeg","webp"]:
                image_part = make_image_data(path)
                source_parts.append(f"IMAGE FILE: {safe_name} (analyze the image)")
            elif ext in ["mp4","mov","avi","mkv","webm","m4v"]:
                # Lightweight, reliable MVP: send filename/context to the model and
                # ask the user to provide a transcript if exact speech content matters.
                source_parts.append(
                    f"VIDEO FILE: {safe_name}. Video is accepted by the dashboard. "
                    "For exact spoken content, include a transcript in the text box."
                )
            else:
                extracted = file_to_text(path)
                source_parts.append(f"DOCUMENT FILE: {safe_name}\n{extracted[:120000]}")

        source = "\n\n".join(source_parts)
        full_prompt = build_prompt(
            source, audience, tone, language, detail, objective, style, selected
        )

        content = [{"type": "input_text", "text": full_prompt}]
        if image_part:
            content.append({"type": "input_image", "image_url": image_part})

        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
            input=[{"role": "user", "content": content}]
        )

        return jsonify(
            success=True,
            result=response.output_text,
            selected=selected
        )

    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True)
