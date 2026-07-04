# SAHAY: Demo Video Script (2 minutes)

**Goal:** prove it works, and that it works OFFLINE. The single most convincing moment is turning the network off on camera. Keep it tight, judges watch dozens of these.

**Setup before recording**
1. Start the app: in the `sahay` folder run `python -m uvicorn app.server:app --port 8000`.
2. Open `http://localhost:8000` in your browser, full screen.
3. Record with **Xbox Game Bar** (`Win + Alt + R`) or OBS. 1080p.
4. Have one photo ready on the phone/disk: a wound OR a medicine strip.
5. Speak slowly and clearly. Total target: ~2:00.

---

### Shot 1: The hook (0:00–0:20)
**Screen:** SAHAY home screen. Point cursor at the top status bar.
**Say:**
> "When Cyclone Amphan hit Kolkata, the power and the mobile network were gone for days. This is SAHAY, a disaster companion built on Google's Gemma 4 that runs completely offline. Watch the top bar."

**Do:** Turn off Wi-Fi now (click the Windows network icon → disconnect). The NETWORK light flips to red "DEAD". The GEMMA 4 light stays green "ALIVE · LOCAL".
**Say:**
> "Network: dead. Gemma 4: still alive, running right here on this laptop. No internet from this point on."

### Shot 2: Bengali voice → first aid (0:20–0:50)
**Do:** Hold the mic button and speak in Bengali:
> "প্রচুর রক্ত পড়ছে, কী করব?" *(There's heavy bleeding, what do I do?)*
Release.
**Say (while it responds):**
> "I asked in Bengali, by voice. Gemma 4 understood the speech, pulled the verified first-aid protocol from the on-device knowledge base, and is answering in calm, step-by-step Bengali, all with the network off."
**Do:** Let the numbered Bengali steps finish rendering. Scroll so they're visible.

### Shot 3: Vision (0:50–1:15)
**Do:** Click the camera button, attach the medicine-strip (or wound) photo, then type or say: "এটা কী ওষুধ? মেয়াদ আছে?" *(What medicine is this? Is it in date?)*
**Say:**
> "After a flood, people find soaked, unreadable medicine strips. I show Gemma 4 a photo, it reads the label and tells me, in plain Bengali, what it is and whether it's expired. Vision, OCR, and translation in one offline step."

### Shot 4: It acts: SOS + shelter (1:15–1:50)
**Do:** Type/say:
> "Water is rising fast in Kakdwip, my grandmother can't walk, we are 4 people. Help!"
**Say (as the tool chip appears):**
> "Now the important part, Gemma 4 doesn't just talk, it acts. See that? It decided on its own to call the SOS tool, with critical severity and four people. Look at the right panel."
**Do:** Point to the SOS OUTBOX card, the queued message with location and severity. Then trigger a shelter query ("nearest shelter in Namkhana") and point to the shelter card.
**Say:**
> "The SOS is queued in an outbox, it'll send the instant any network returns. It also found the nearest cyclone shelter from an offline registry, and it keeps a family check-in board for reunification."

### Shot 5: Close (1:50–2:00)
**Say:**
> "One open model, Gemma 4 E4B, doing Bengali voice, vision, grounded first aid, and function calling, fully offline on a normal laptop. When the network dies, help shouldn't. That's SAHAY."
**Screen:** End on the home screen with the red NETWORK / green GEMMA bar visible.

---

**Tips**
- If a response is slow, cut the dead air in editing, don't wait on camera.
- Keep the Wi-Fi-off moment; it's the whole pitch.
- Add one caption at the start: "Wi-Fi is OFF for this entire demo."
- Export as MP4, upload to YouTube (unlisted is fine) or attach the file to the writeup.
