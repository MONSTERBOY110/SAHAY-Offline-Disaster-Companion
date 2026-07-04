"""Native function-calling tools for SAHAY.

Gemma 4 decides when to call these; each one performs a real local action,
queueing an SOS SMS in the outbox, searching the offline shelter registry,
looking up first-aid protocols, or updating the family check-in board.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from . import rag

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTBOX_FILE = DATA_DIR / "outbox.json"
FAMILY_FILE = DATA_DIR / "family.json"
SHELTERS_FILE = ROOT / "knowledge" / "shelters.json"
HELPLINES_FILE = ROOT / "knowledge" / "helplines.json"


def _load(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def _save(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- tool bodies

def queue_sos_sms(location: str, situation: str, severity: str = "high",
                  people_affected: int = 1) -> dict:
    outbox = _load(OUTBOX_FILE, [])
    sms_body = (
        f"SOS via SAHAY | Severity: {severity.upper()} | {situation} | "
        f"Location: {location} | People: {people_affected} | "
        f"Queued: {time.strftime('%d %b %Y %H:%M')}"
    )
    entry = {
        "id": uuid.uuid4().hex[:8],
        "to": "112 (ERSS) + 1070 (WB Disaster Mgmt)",
        "body": sms_body,
        "location": location,
        "severity": severity,
        "status": "queued_offline",
        "queued_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    outbox.append(entry)
    _save(OUTBOX_FILE, outbox)
    return {
        "queued": True,
        "sms_id": entry["id"],
        "message": "SOS queued in the offline outbox. It will transmit automatically "
                   "the moment any network (SMS/2G) returns. Keep the phone charged.",
        "sms_preview": sms_body,
    }


def find_nearest_shelter(area: str) -> dict:
    data = _load(SHELTERS_FILE, {"shelters": []})
    shelters = data.get("shelters", [])
    q = area.strip().lower()
    scored = []
    for s in shelters:
        haystack = " ".join(
            str(s.get(f, "")) for f in ("name", "name_bn", "district", "block_or_area", "landmark")
        ).lower()
        score = sum(1 for word in q.split() if word in haystack)
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    matches = [s for _, s in scored[:3]]
    if not matches:
        matches = shelters[:3]
    return {
        "query": area,
        "shelters": [
            {
                "name": s["name"],
                "name_bn": s.get("name_bn", ""),
                "district": s["district"],
                "area": s.get("block_or_area", ""),
                "landmark": s.get("landmark", ""),
                "capacity": s.get("capacity"),
                "facilities": s.get("facilities", []),
            }
            for s in matches
        ],
        "note": data.get("note", ""),
    }


def first_aid_lookup(topic: str) -> dict:
    chunks = rag.kb().search(topic, k=3)
    return {
        "topic": topic,
        "protocols": [{"section": c.label, "guidance": c.text} for c in chunks],
    }


def log_family_member(name: str, status: str, location: str = "") -> dict:
    family = _load(FAMILY_FILE, [])
    entry = {
        "name": name,
        "status": status,
        "location": location,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    family = [f for f in family if f["name"].lower() != name.lower()]
    family.append(entry)
    _save(FAMILY_FILE, family)
    return {"logged": True, "family_board": family}


def get_helplines() -> dict:
    return {"helplines": _load(HELPLINES_FILE, [])}


# ------------------------------------------------------------- tool registry

TOOL_FUNCTIONS = {
    "queue_sos_sms": queue_sos_sms,
    "find_nearest_shelter": find_nearest_shelter,
    "first_aid_lookup": first_aid_lookup,
    "log_family_member": log_family_member,
    "get_helplines": get_helplines,
}

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "queue_sos_sms",
            "description": "Queue an emergency SOS SMS in the offline outbox, to be sent "
                           "to rescue services (112 / WB disaster helpline 1070) as soon as "
                           "any network returns. Use when someone needs rescue, is trapped, "
                           "seriously injured, or in danger.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Best known location: area, landmark, village, ward"},
                    "situation": {"type": "string", "description": "One-line description of the emergency"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "people_affected": {"type": "integer", "description": "How many people need help"},
                },
                "required": ["location", "situation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest_shelter",
            "description": "Search the offline registry of West Bengal cyclone shelters and "
                           "flood relief centres by area, district, or landmark. Use when the "
                           "user asks where to go, needs evacuation, or needs a safe place.",
            "parameters": {
                "type": "object",
                "properties": {
                    "area": {"type": "string", "description": "Area, district, block or landmark the user mentions"},
                },
                "required": ["area"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "first_aid_lookup",
            "description": "Retrieve verified offline first-aid and disaster-safety protocols "
                           "(bilingual English/Bengali) for a medical topic, e.g. bleeding, "
                           "snakebite, drowning, fracture, burns, diarrhea, water purification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The medical or safety topic to look up"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_family_member",
            "description": "Record a family member's safety status on the offline family "
                           "check-in board (used for reunification when networks return). "
                           "Use when the user reports someone safe, missing, or injured.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["safe", "missing", "injured", "evacuated"]},
                    "location": {"type": "string"},
                },
                "required": ["name", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_helplines",
            "description": "List official Indian emergency helpline numbers (112, 108, WB "
                           "disaster management 1070, etc). Use when the user asks whom to call.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def execute_tool(name: str, args: dict) -> dict:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**args)
    except TypeError as exc:
        return {"error": f"Bad arguments for {name}: {exc}"}
