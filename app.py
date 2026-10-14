import os
import mimetypes
import time
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

ALLOWED = {
    "txt", "md", "pdf", "docx",
    "png", "jpg", "jpeg", "webp",
    "mp4", "mov", "avi", "mkv", "webm", "m4v"
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
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Create a .env file and add your Gemini API key."
        )

    return genai.Client(api_key=key)


def file_to_text(path):
    ext = path.suffix.lower()

    if ext in [".txt", ".md"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            import pypdf

            reader = pypdf.PdfReader(str(path))

            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except Exception as e:
            return f"[PDF extraction failed: {e}]"

    if ext == ".docx":
        try:
            from docx import Document

            doc = Document(str(path))

            return "\n".join(
                p.text
                for p in doc.paragraphs
            )

        except Exception as e:
            return f"[DOCX extraction failed: {e}]"

    return ""


def build_prompt(
    source,
    audience,
    tone,
    language,
    detail,
    objective,
    style,
    selected
):
    output_instructions = "\n".join(
        f"{i}. {OUTPUTS[k]}"
        for i, k in enumerate(selected, 1)
    )

    return f"""
You are the GenAI engine of an automated content transformation platform.

INNOVATIVE FEATURE — AUDIENCE-AWARE PERSONALIZATION:

Before creating the outputs, adapt the source to the selected target
audience's knowledge level, needs, communication preferences and purpose.

The same source must be transformed differently when the audience changes.

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

RULES:

- Do not invent facts.
- Preserve important names, numbers, dates and claims from the source.
- If information is missing, clearly label assumptions instead of fabricating facts.
- Tailor wording, terminology, depth and examples to the selected audience.
- Keep all selected deliverables consistent with the same source.
- Return clean Markdown with a separate heading for every selected output.
- Make each output ready to copy/use.
"""


def generate_with_retry(client, model, contents, max_retries=3):
    """
    Generate Gemini content with automatic retry handling.

    Handles temporary 503 / UNAVAILABLE errors and similar
    transient API failures.
    """

    last_error = None

    for attempt in range(max_retries):
        try:
            print(
                f"Generating content using {model} "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            response = client.models.generate_content(
                model=model,
                contents=contents
            )

            return response

        except Exception as e:
            last_error = e
            error_text = str(e)

            print(f"Gemini API error: {error_text}")

            # Temporary server overload / unavailable model
            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text.upper()
                or "high demand" in error_text.lower()
                or "temporarily unavailable" in error_text.lower()
            ):
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)

                    print(
                        f"Temporary Gemini error. "
                        f"Retrying in {wait_time} seconds..."
                    )

                    time.sleep(wait_time)
                    continue

            # For non-temporary errors, stop immediately.
            raise e

    raise last_error


def generate_content_with_fallback(client, contents):
    """
    Try the configured Gemini model first.

    If it is temporarily unavailable, try fallback models.
    """

    primary_model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.8-flash"
    )

    fallback_models = [
        primary_model,
        "gemini-2.5-flash",
        "gemini-2.0-flash"
    ]

    # Remove duplicates while preserving order
    models_to_try = list(dict.fromkeys(fallback_models))

    errors = []

    for model in models_to_try:

        try:
            response = generate_with_retry(
                client,
                model,
                contents,
                max_retries=3
            )

            print(f"Successfully generated using model: {model}")

            return response, model

        except Exception as e:
            error_text = str(e)

            errors.append(
                f"{model}: {error_text}"
            )

            print(
                f"Model {model} failed: {error_text}"
            )

            # Try next fallback model
            continue

    # All models failed
    raise RuntimeError(
        "Gemini generation failed after trying all available models.\n\n"
        + "\n".join(errors)
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/transform")
def transform():

    temp_path = None

    try:

        client = get_client()

        # -----------------------------------------
        # GET FORM DATA
        # -----------------------------------------

        audience = request.form.get(
            "audience",
            "General"
        )

        tone = request.form.get(
            "tone",
            "Professional"
        )

        language = request.form.get(
            "language",
            "English"
        )

        detail = request.form.get(
            "detail",
            "Medium"
        )

        objective = request.form.get(
            "objective",
            "Inform"
        )

        style = request.form.get(
            "style",
            "Clear and professional"
        )

        selected = request.form.getlist(
            "outputs"
        )

        user_text = request.form.get(
            "source_text",
            ""
        ).strip()

        # -----------------------------------------
        # VALIDATE OUTPUT SELECTION
        # -----------------------------------------

        if not selected:

            return jsonify(
                error="Select at least one output format."
            ), 400

        # -----------------------------------------
        # VALIDATE SOURCE
        # -----------------------------------------

        uploaded = request.files.get("file")

        if not user_text and not (
            uploaded and uploaded.filename
        ):

            return jsonify(
                error="Enter source text or upload a file."
            ), 400

        # -----------------------------------------
        # SOURCE CONTENT
        # -----------------------------------------

        source_parts = []
        media_parts = []

        # User entered text
        if user_text:

            source_parts.append(
                "USER-PROVIDED TEXT:\n" + user_text
            )

        # -----------------------------------------
        # FILE PROCESSING
        # -----------------------------------------

        if uploaded and uploaded.filename:

            ext = (
                Path(uploaded.filename)
                .suffix
                .lower()
                .lstrip(".")
            )

            if ext not in ALLOWED:

                return jsonify(
                    error=f"Unsupported file type: .{ext}"
                ), 400

            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)

            safe_name = Path(
                uploaded.filename
            ).name

            temp_path = temp_dir / safe_name

            uploaded.save(temp_path)

            # -------------------------------------
            # IMAGE
            # -------------------------------------

            if ext in {
                "png",
                "jpg",
                "jpeg",
                "webp"
            }:

                mime = (
                    mimetypes.guess_type(
                        temp_path.name
                    )[0]
                    or "image/jpeg"
                )

                image_part = types.Part.from_bytes(
                    data=temp_path.read_bytes(),
                    mime_type=mime
                )

                media_parts.append(
                    image_part
                )

                source_parts.append(
                    f"IMAGE FILE: {safe_name}. "
                    "Analyze the image together "
                    "with the source text."
                )

            # -------------------------------------
            # VIDEO
            # -------------------------------------

            elif ext in {
                "mp4",
                "mov",
                "avi",
                "mkv",
                "webm",
                "m4v"
            }:

                print(
                    f"Uploading video: {safe_name}"
                )

                video_file = client.files.upload(
                    file=str(temp_path)
                )

                print(
                    "Waiting for video processing..."
                )

                for _ in range(60):

                    state = getattr(
                        video_file,
                        "state",
                        None
                    )

                    state_name = getattr(
                        state,
                        "name",
                        str(state)
                    )

                    print(
                        f"Video state: {state_name}"
                    )

                    if state_name == "ACTIVE":
                        break

                    if state_name == "FAILED":

                        raise RuntimeError(
                            "Gemini could not process "
                            "the uploaded video."
                        )

                    time.sleep(5)

                    video_file = client.files.get(
                        name=video_file.name
                    )

                else:

                    raise RuntimeError(
                        "Video processing timed out. "
                        "Try a shorter/smaller video."
                    )

                media_parts.append(
                    video_file
                )

                source_parts.append(
                    f"VIDEO FILE: {safe_name}. "
                    "Analyze the visual and spoken "
                    "content of the video when relevant."
                )

            # -------------------------------------
            # DOCUMENT
            # -------------------------------------

            else:

                extracted = file_to_text(
                    temp_path
                )

                if extracted.strip():

                    source_parts.append(
                        f"DOCUMENT FILE: {safe_name}\n"
                        f"{extracted[:120000]}"
                    )

                else:

                    try:

                        doc_file = client.files.upload(
                            file=str(temp_path)
                        )

                        media_parts.append(
                            doc_file
                        )

                        source_parts.append(
                            f"DOCUMENT FILE: {safe_name}. "
                            "Analyze this document directly."
                        )

                    except Exception:

                        source_parts.append(
                            f"DOCUMENT FILE: {safe_name}. "
                            "No readable text was extracted."
                        )

        # -----------------------------------------
        # BUILD SOURCE
        # -----------------------------------------

        source = "\n\n".join(
            source_parts
        )

        if not source.strip():

            return jsonify(
                error="No readable source content was found."
            ), 400

        # -----------------------------------------
        # BUILD PROMPT
        # -----------------------------------------

        prompt = build_prompt(
            source,
            audience,
            tone,
            language,
            detail,
            objective,
            style,
            selected
        )

        # -----------------------------------------
        # BUILD GEMINI CONTENTS
        # -----------------------------------------

        contents = [prompt]

        contents.extend(
            media_parts
        )

        # -----------------------------------------
        # GENERATE WITH RETRY + FALLBACK
        # -----------------------------------------

        response, used_model = (
            generate_content_with_fallback(
                client,
                contents
            )
        )

        # -----------------------------------------
        # GET RESULT
        # -----------------------------------------

        result_text = getattr(
            response,
            "text",
            None
        )

        if not result_text:

            raise RuntimeError(
                "Gemini returned an empty response. "
                "Try shorter source content."
            )

        # -----------------------------------------
        # SUCCESS
        # -----------------------------------------

        return jsonify(
            success=True,
            result=result_text,
            selected=selected,
            model=used_model
        )

    # ---------------------------------------------
    # ERROR HANDLING
    # ---------------------------------------------

    except Exception as e:

        error_text = str(e)

        print(
            "\n========== ERROR =========="
        )

        print(error_text)

        print(
            "===========================\n"
        )

        return jsonify(
            error=error_text
        ), 500

    # ---------------------------------------------
    # CLEAN TEMP FILE
    # ---------------------------------------------

    finally:

        if (
            temp_path
            and temp_path.exists()
        ):

            try:

                temp_path.unlink()

            except Exception as cleanup_error:

                print(
                    f"Could not delete temporary file: "
                    f"{cleanup_error}"
                )


# ---------------------------------------------
# START FLASK APPLICATION
# ---------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
