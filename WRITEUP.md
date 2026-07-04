# সহায় SAHAY: the disaster companion that works when nothing else does

**Track: GenAI for Good** · Team TeesMaarKhaCoders (Chandan Saha, Aritra Giri, Subhojyoti Maity)
Code: https://github.com/MONSTERBOY110/sahay · Demo notebook: kaggle.com/code/subhojyoti110/sahay-gemma4-demo

## The problem we could not stop thinking about

On 20 May 2020, Cyclone Amphan made landfall near Kolkata. It killed ~100 people and left large parts of South Bengal without electricity or mobile network **for days**. The families who most needed information, how to stop a bleeding wound, whether the water was safe to drink, where the nearest shelter was, how to tell a rescuer where they were trapped, were the ones who had been cut off from every source of it.

This is the cruel irony of disaster tech: the moment a person needs an AI assistant the most is the exact moment the internet vanishes. Every cloud chatbot is useless in a cyclone by design.

We asked a different question: **what if the assistant did not need the network at all?**

## The insight: Gemma 4 makes offline frontier AI real

Gemma 4 E4B is the first open model that puts everything a disaster companion needs onto a device that survives a blackout, a laptop on a power bank, or a phone:

- **Bengali** (among 140+ languages) so victims speak naturally, not in English
- **native audio** so a panicking, possibly illiterate person can just *talk*
- **native vision** so they can show a wound, a flooded street, a medicine strip
- **native function calling** so the model can *act*, not just chat
- small enough (~8B, 4-bit) to run at conversational speed on a 6 GB laptop GPU

SAHAY is what we built on top of it: an offline-first companion where the model, the medical knowledge, and the tools all live on the device. We tested it the only way that matters, **with the Wi-Fi switched off.**

## What SAHAY does (all offline)

1. **Speak the emergency in Bengali.** *"প্রচুর রক্ত পড়ছে, কী করব?"* SAHAY understands the speech, retrieves the verified bleeding-control protocol, and answers in calm, numbered Bengali steps.
2. **Show it.** A photo of a wound → severity triage. A flooded room → damage read. A soaked medicine strip → SAHAY reads the label aloud in simple Bengali and says whether it is expired. (Verified live: it correctly read "Paracetamol / Calpol-500, Exp 12/2028, still valid" from a photo.)
3. **It acts, it doesn't just talk.** Gemma 4's function calling drives real local tools:
   - `queue_sos_sms` builds a structured SOS (location, injury, severity, headcount) and queues it in an **outbox** that transmits the instant any network flickers back.
   - `find_nearest_shelter` searches an offline West Bengal cyclone-shelter registry.
   - `log_family_member` keeps an offline family check-in board for reunification.
   - `first_aid_lookup` and `get_helplines` surface verified protocols and real Indian emergency numbers (112, 108, 1070…).

In our live test, told *"Water is rising fast in Kakdwip, my grandmother cannot walk, we are 4 people,"* Gemma 4 **decided on its own** to call `queue_sos_sms` with `severity: critical, people_affected: 4` and a clear situation summary, then explained to the user, in Bengali, that the SOS was queued and would send when the network returned.

## How it is built

```
 Browser UI (voice · camera · Bengali chat)   ← no CDN assets, works offline
        │  HTTP (localhost)
 FastAPI backend  (app/server.py)
        │
        ├─ BM25 RAG over knowledge/  (86 chunks: bilingual first-aid,
        │   cyclone/flood preparedness, shelter & helpline registries)
        ├─ native function-calling loop  (5 tools, executed locally)
        │
        ▼
 Ollama ── Gemma 4 E4B  (text + vision + audio, tools, 128K ctx)
```

**Gemma 4 is the single brain.** It interprets Bengali speech and photos, chooses which tool to call, grounds every medical answer in retrieved protocol chunks, and replies in the user's own language. Retrieval keeps the model honest: first-aid steps come from a curated IFRC/WHO-style corpus, not from open-ended generation, which matters when the output is read aloud to someone in danger.

## The 24-hour engineering story (and why our choices were right)

**Why E4B, not a bigger Gemma.** The whole thesis is "runs where the network is dead." We deliberately targeted the edge model that fits a mid-range laptop (we developed on an RTX 3050, 6 GB) and would fit a phone. Choosing the flashier 31B would have quietly broken the one promise that makes SAHAY matter.

**Why offline RAG over fine-tuning.** In a one-day sprint, BM25 retrieval over a hand-curated bilingual corpus gave us grounded, auditable medical answers with zero training time and zero extra model weight, and it is trivially updatable with the official shelter registry in production.

**The real bug we hit, and how we handled it.** Mid-build we discovered a current Ollama regression (ollama/ollama#16874) where Gemma 4 E4B silently drops **image** inputs at the API layer, while text and tools work perfectly. Rather than fake it, we engineered around it honestly: SAHAY routes vision turns to Gemma-4-12B (same family, image ingestion unaffected) and keeps E4B for latency-critical text and agentic turns, using a modality-aware router in `server.py`. Our Kaggle notebook demonstrates E4B doing native vision **and** audio directly via `transformers`, proving the limitation is today's runtime, not the model. For voice, when the runtime does not yet expose Gemma 4's audio encoder we fall back to a local Whisper model, still 100% offline. Being upfront about this is the point: disaster software that pretends to work is worse than useless.

## Impact

Bengal faces a cyclone almost every year (Amphan 2020, Yaas 2021, Remal 2024). SAHAY is a template for the class of tool that has been impossible until now: **frontier AI that shows up precisely when the infrastructure has left.** The same offline architecture, Bengali/Hindi voice + vision + grounded guidance + queued action, extends directly to rural clinics, fishing boats out of coverage, and the first 72 hours of any disaster anywhere. It is open-source (MIT) so any relief organization can deploy and extend it.

When the network dies, help shouldn't. That is what Gemma 4 finally makes possible.
