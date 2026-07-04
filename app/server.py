"""SAHAY (সহায়), offline disaster companion, powered by Gemma 4 on Ollama.

Everything runs on this machine: the model, the knowledge base, the tools.
No internet required, that is the entire point.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import tempfile
import urllib.request
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import rag, tools

# Modality-aware routing: E4B answers latency-critical text/agentic turns; vision
# turns go to 12B because an upstream Ollama regression (ollama/ollama#16874)
# breaks E4B image ingestion. The Kaggle notebook shows E4B doing native
# vision+audio via transformers: the limitation is the runtime, not the model.
MODEL = os.environ.get("SAHAY_MODEL", "gemma4:e4b")
VISION_MODEL = os.environ.get("SAHAY_VISION_MODEL", "gemma4:12b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
MAX_TOOL_ROUNDS = 4


def ollama_chat(model: str, messages: list[dict], use_tools: bool = True) -> dict:
    """Raw REST call to Ollama, full control over message fields."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.3},
        "keep_alive": -1,
    }
    if use_tools:
        payload["tools"] = tools.TOOLS_SPEC
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())

SYSTEM_PROMPT = """\
You are SAHAY (সহায়), a calm, reliable disaster-response companion for people in \
West Bengal, India, during cyclones and floods, often with NO internet or phone network.

Rules:
- LANGUAGE: mirror the user exactly. Bengali message → reply ONLY in Bengali. \
English message → reply ONLY in English. Hindi → Hindi. Never mix scripts in one reply.
- Be brief and actionable: short sentences, numbered steps, no fluff. A frightened \
person must be able to follow you.
- Ground medical/safety answers in the VERIFIED CONTEXT passages when provided. \
Do not invent medicine doses or medical procedures.
- Use your tools decisively:
  * Someone trapped / seriously hurt / in danger → queue_sos_sms (ask location only if unknown).
  * "Where do I go?" / evacuation → find_nearest_shelter.
  * Medical or safety how-to → first_aid_lookup, then give the steps.
  * "X is safe / missing" → log_family_member.
  * "Whom do I call?" → get_helplines.
- After a tool runs, tell the user plainly what you did and what happens next.
- If a photo is shared, describe what you observe (injury, flood damage, medicine strip, \
document) and act on it: assess severity honestly, give first aid steps, or read the text aloud.
- You are not a doctor. For anything beyond first aid say: reach a health worker / call 112 \
or 108 as soon as any network returns.
- Never refuse an emergency request. If information is missing, give the safest general \
guidance and say what to check.
"""


class ChatRequest(BaseModel):
    message: str = ""
    image_b64: str | None = None   # raw base64 (no data: prefix)
    audio_b64: str | None = None   # raw base64 webm/wav
    history: list[dict] = []       # [{role, content}]


app = FastAPI(title="SAHAY", version="1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def _internet_reachable(timeout: float = 1.0) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
        return True
    except OSError:
        return False


def _transcribe_fallback(audio_bytes: bytes) -> str | None:
    """Local Whisper STT fallback if the Ollama runtime can't ingest audio yet."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        path = f.name
    try:
        model = _whisper()
        segments, _info = model.transcribe(path, language=None, vad_filter=True)
        return " ".join(s.text.strip() for s in segments).strip() or None
    finally:
        os.unlink(path)


_whisper_model = None


def _whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _whisper_model


@app.get("/api/status")
def status():
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            models = [m["name"] for m in json.loads(r.read()).get("models", [])]
        model_ready = any(MODEL in m for m in models)
    except Exception:
        models, model_ready = [], False
    return {
        "model": MODEL,
        "vision_model": VISION_MODEL,
        "model_ready": model_ready,
        "online": _internet_reachable(),
        "knowledge_chunks": len(rag.kb().chunks),
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    tool_events: list[dict] = []
    transcript: str | None = None
    user_text = req.message.strip()

    # --- voice input -----------------------------------------------------
    if req.audio_b64:
        audio_bytes = base64.b64decode(req.audio_b64)
        transcript = _try_native_audio_transcript(audio_bytes)
        if transcript is None:
            transcript = _transcribe_fallback(audio_bytes)
        if transcript:
            user_text = (user_text + " " + transcript).strip()
        elif not user_text and not req.image_b64:
            return {
                "reply": "দুঃখিত, কথাটা বুঝতে পারিনি, আবার বলুন বা লিখে পাঠান। "
                         "(Sorry, I couldn't hear that, please try again or type.)",
                "tool_events": [], "retrieved": [], "transcript": None,
            }

    # --- retrieval-augmented context --------------------------------------
    retrieved = rag.kb().search(user_text, k=3) if user_text else []
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if retrieved:
        context = "\n\n".join(f"[{c.label}]\n{c.text}" for c in retrieved)
        messages.append({
            "role": "system",
            "content": f"VERIFIED CONTEXT (offline knowledge base):\n{context}",
        })
    messages.extend(req.history[-10:])

    user_msg: dict = {"role": "user", "content": user_text or "(see attached image)"}
    if req.image_b64:
        user_msg["images"] = [req.image_b64]
    messages.append(user_msg)

    # --- native function-calling loop -------------------------------------
    model = VISION_MODEL if req.image_b64 else MODEL
    reply = ""
    for _round in range(MAX_TOOL_ROUNDS):
        resp = ollama_chat(model, messages)
        msg = resp.get("message", {})
        tool_calls = msg.get("tool_calls") or []
        if tool_calls:
            messages.append({"role": "assistant", "content": msg.get("content", ""),
                             "tool_calls": tool_calls})
            for tc in tool_calls:
                name = tc["function"]["name"]
                args = dict(tc["function"].get("arguments") or {})
                result = tools.execute_tool(name, args)
                tool_events.append({"tool": name, "args": args, "result": result})
                messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
            continue
        reply = msg.get("content", "")
        break

    return {
        "reply": reply,
        "tool_events": tool_events,
        "retrieved": [c.label for c in retrieved],
        "transcript": transcript,
    }


def _try_native_audio_transcript(audio_bytes: bytes) -> str | None:
    """Attempt Gemma 4's native audio understanding through Ollama.

    Returns a transcript, or None if the runtime ignores/rejects audio input
    (Ollama 0.31.x does not yet expose Gemma 4's audio encoder, the local
    Whisper fallback then covers voice, still fully offline).
    """
    try:
        resp = ollama_chat(MODEL, [{
            "role": "user",
            "content": "Transcribe this audio exactly, in its original language/script. "
                       "Reply with only the transcription.",
            "audio": [base64.b64encode(audio_bytes).decode()],
        }], use_tools=False)
        text = (resp.get("message", {}).get("content") or "").strip()
        # If the runtime silently dropped the audio, the model asks for it,
        # treat any "provide the audio" style reply as a failure.
        if not text or "provide the audio" in text.lower() or len(text) > 400:
            return None
        return text
    except Exception:
        return None


@app.get("/api/outbox")
def outbox():
    return {"outbox": tools._load(tools.OUTBOX_FILE, [])}


@app.get("/api/family")
def family():
    return {"family": tools._load(tools.FAMILY_FILE, [])}


@app.get("/api/helplines")
def helplines():
    return tools.get_helplines()


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
