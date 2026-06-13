import base64
import io


def process_upload(content_bytes: bytes, filename: str) -> dict:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("png", "jpg", "jpeg", "gif", "webp"):
        encoded = base64.b64encode(content_bytes).decode("utf-8")
        # Ensure standard mime format
        mime_ext = "jpeg" if ext == "jpg" else ext
        return {
            "type": "image",
            "content": encoded,
            "filename": filename,
            "media_type": f"image/{mime_ext}",
        }

    if ext == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            text = f"[PDF parsing failed: {e}]"
        return {
            "type": "text",
            "content": f"[PDF: {filename}]\n{text}",
            "filename": filename,
        }

    if ext == "csv":
        try:
            import pandas as pd
            df = pd.read_csv(io.BytesIO(content_bytes))
            text = df.to_markdown(index=False)
        except Exception as e:
            text = f"[CSV parsing failed: {e}]"
        return {
            "type": "text",
            "content": f"[CSV: {filename}]\n{text}",
            "filename": filename,
        }

    # Default: plain text / binary fallback
    try:
        text = content_bytes.decode("utf-8")
        content_str = f"[File: {filename}]\n{text}"
    except UnicodeDecodeError:
        content_str = f"[Binary file: {filename}, {len(content_bytes)} bytes]"

    return {
        "type": "text",
        "content": content_str,
        "filename": filename,
    }
