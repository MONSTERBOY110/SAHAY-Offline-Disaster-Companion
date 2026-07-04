# সহায় SAHAY: the offline disaster companion

**When the network dies, help shouldn't.**

SAHAY is an offline-first, multimodal disaster-response companion for cyclone- and
flood-affected West Bengal, built on **Google DeepMind's Gemma 4 (E4B)** running fully
locally via Ollama. No internet, no cloud, no API key: the model, the knowledge, and
the tools all live on the device.

Built in 24 hours for the **Build with Gemma: Kolkata** hackathon (Kaggle) by
**Team TeesMaarKhaCoders**: Chandan Saha, Aritra Giri, Subhojyoti Maity.
Track: **GenAI for Good**.

## Why offline is the whole point

When Cyclone Amphan hit Kolkata in May 2020, power and mobile networks were down for
days across South Bengal. The moment people need information the most, first aid,
where the shelters are, how to make water safe, is exactly the moment the internet
disappears. Every cloud chatbot fails this test by design.

Gemma 4's edge models change that: frontier-quality reasoning, **Bengali among 140+
languages**, **native audio and vision**, and **native function calling**, in a model
that runs on a mid-range laptop GPU (RTX 3050, 6 GB), or a phone.

![SAHAY UI](assets/ui-home.png)

*A live turn: the user reports a missing grandmother in Bengali → Gemma 4 calls
`log_family_member` on its own → the Family Board updates, all offline:*

![Family board update](assets/ui-family-board.png)

## What it does

| You do | SAHAY does |
|---|---|
| Speak in Bengali: *"প্রচুর রক্ত পড়ছে, কী করব?"* | Understands the speech, retrieves the verified bleeding-control protocol, answers step by step in Bengali |
| Share a photo of a wound, flooded room, or medicine strip | Gemma 4 vision assesses it: severity triage, damage description, or reads the medicine label aloud in plain Bengali |
| *"I'm trapped near Kakdwip, water is rising"* | Calls `queue_sos_sms` → a structured SOS is queued in the outbox and transmits the instant any network returns |
| *"Where is the nearest shelter?"* | Calls `find_nearest_shelter` → searches the offline West Bengal shelter registry |
| *"বাবা safe আছে"* | Calls `log_family_member` → offline family check-in board for reunification |

## Architecture

```
 ┌────────────── laptop / edge device (no internet) ──────────────┐
 │                                                                │
 │  Browser UI ── voice (MediaRecorder) · camera · Bengali chat   │
 │      │                                                         │
 │  FastAPI backend (app/server.py)                               │
 │      │── BM25 RAG over knowledge/ (bilingual first-aid,        │
 │      │   preparedness, shelters, retrieved per message)       │
 │      │── native function-calling loop:                         │
 │      │     queue_sos_sms · find_nearest_shelter ·              │
 │      │     first_aid_lookup · log_family_member · get_helplines│
 │      ▼                                                         │
 │  Ollama ── Gemma 4 E4B (text + vision + audio, 128K ctx)       │
 └────────────────────────────────────────────────────────────────┘
```

Gemma 4 is the single brain: it understands Bengali speech and photos, decides when
to call tools, grounds its answers in retrieved protocol chunks, and speaks the
user's language back.

## Run it

```bash
# 1. Ollama + model (one-time, ~10 GB)
ollama pull gemma4:e4b

# 2. Backend + UI
pip install -r requirements.txt
uvicorn app.server:app --port 8000

# 3. Open http://localhost:8000 in your browser, then turn your Wi-Fi off.
```

Optional voice fallback if your Ollama build doesn't accept audio yet:
`pip install faster-whisper` (local STT, still fully offline).

## Repository layout

```
app/        FastAPI server, RAG, function-calling tools
web/        offline-first UI (no CDN assets, system Bengali fonts)
knowledge/  bilingual first-aid + preparedness corpus, shelter & helpline registries
notebook/   clonable Kaggle notebook demo (transformers + native audio)
```

## Honesty notes

- The shelter registry is an illustrative sample; production would load the official
  WBSDMA/NDMA shelter database (same schema).
- SAHAY gives standard first-aid guidance (IFRC/WHO-style) and always directs users
  to professional care (112/108) the moment networks return. It is a companion, not
  a doctor.

## License

MIT, see [LICENSE](LICENSE).
