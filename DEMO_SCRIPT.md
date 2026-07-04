# SAHAY: Demo Video Script (about 2 minutes)

Team TeesMaarKhaCoders. Build with Gemma: Kolkata (GenAI for Good).

**Goal:** prove it works, and that it works OFFLINE. The single most convincing
moment is the network being off while Gemma keeps answering. Keep it tight; judges
watch dozens of these.

## Why this wins (say these lines, they map to the judging rubric)

The rubric is Gemma Integration 30, Innovation and Impact 30, Functionality 20,
Presentation 20. Land one sentence for each and the score follows.

1. **Gemma is necessary, not decorative (Gemma Integration, 30).** This is our
   strongest card. Say it out loud: *"The problem requires an open model that runs on
   the device. A cloud API is disqualified, because in a cyclone there is no cloud. So
   Gemma 4 is not a nice-to-have here, it is the only thing that makes this possible."*
   Then show the breadth: Bengali speech in, a photo in, grounded first aid out, and a
   tool call, one model doing all four.
2. **A problem the judges have lived (Innovation and Impact, 30).** These are Kolkata
   judges. Name it: *"When Amphan hit, this city had no power and no network for days.
   The moment people needed information the most was the exact moment the internet was
   gone."* Local plus life-safety plus a real paradox.
3. **It visibly does something a cloud app cannot (Functionality, 20).** The Wi-Fi-off
   badge plus the autonomous SOS tool call is the proof. Do not just claim it works,
   show the network dead and the model still acting.
4. **Honesty reads as competence (Presentation, 20).** One line: *"We hit a real bug,
   Gemma 4 image input is broken in the current Ollama build, so we routed vision to
   the 12B model and said so. We would rather ship something true than fake a demo."*
   Judges trust teams that show their scars.

Closing differentiator to repeat once: **"Every other assistant fails the moment the
network dies. Ours is built for exactly that moment."**

## Setup before recording

1. Start the app from the `sahay` folder:
   `python -m uvicorn app.server:app --port 8000`
2. Warm the models so responses are fast on camera (do this once, right before recording):
   send one throwaway Bengali message, and attach one throwaway photo. The first photo
   takes about 30 to 60 seconds while the vision model loads into the 6 GB GPU; after
   that, photos are quick. Text and voice stay fast once warmed.
3. Open `http://localhost:8000` in Chrome, full screen. The left sidebar STATUS panel
   should read **Network: DEAD** (red) if Wi-Fi is already off, and **Gemma 4: ALIVE ·
   LOCAL** (amber).
4. Record with Xbox Game Bar (`Win + Alt + R`) or OBS, 1080p.
5. Have one photo ready: a medicine strip or a wound.
6. Type Bengali directly in the browser box; it handles Unicode correctly.

## Shot 1: The hook (0:00 to 0:20)

**Screen:** SAHAY home screen. Point the cursor at the STATUS panel in the left sidebar.
**Say:**
> "When Cyclone Amphan hit Kolkata, power and mobile networks were gone for days.
> This is SAHAY, a disaster companion built on Google's Gemma 4 that runs completely
> offline. Watch the status panel."

**Do:** If Wi-Fi is still on, turn it off now (Windows network icon, disconnect).
Network flips to red "DEAD"; Gemma 4 stays amber "ALIVE · LOCAL" with a live heartbeat.
**Say:**
> "Network: dead. Gemma 4: still alive, running right here on this laptop.
> No internet from this point on. This is the point: in a cyclone there is no cloud,
> so a cloud AI is useless. Only an open, on-device model like Gemma 4 can help, which
> is why Gemma is the heart of this project, not a feature bolted on."

## Shot 2: Bengali voice to first aid (0:20 to 0:50)

**Do:** Hold the mic button and speak in Bengali, or tap the রক্তপাত chip in the composer, or type:
> `প্রচুর রক্ত পড়ছে, কী করব?`  *(There is heavy bleeding, what do I do?)*

**Say (while it responds):**
> "I asked in Bengali, by voice. Gemma 4 understood the speech, pulled the verified
> first-aid protocol from the on-device knowledge base, and is answering in calm,
> step-by-step Bengali, all with the network off."

**Do:** Let the numbered Bengali steps finish. A small "first_aid_lookup" tool chip may
also appear, that is Gemma retrieving the protocol. Scroll so the steps are visible.

*(Backup prompt if you want a second example: `সাপে কামড়েছে, পা ফুলে যাচ্ছে। এখন কী করব?`
"a snake has bitten, the leg is swelling, what now". It gives the India-specific
snakebite steps: immobilize, no tourniquet, no cutting, get to hospital.)*

## Shot 3: It acts, it does not just talk (0:50 to 1:25)

This is the strongest shot. **Do:** type or say:
> "Water is rising fast in Kakdwip, my grandmother cannot walk. We are 4 people. Help!"

**Say (as the tool chip appears):**
> "Now the important part: Gemma 4 does not just talk, it acts. It decided on its own
> to call the SOS tool, with critical severity and four people. Look at the sidebar."

**Do:** Point to the **SOS OUTBOX** in the left sidebar, the queued message with location
and severity and the "sends when network returns" line.
**Then** ask for a shelter (tap the আশ্রয়কেন্দ্র chip or type):
> `আমার কাছের আশ্রয়কেন্দ্র কোথায়? আমি আছি নামখানা`  *(where is my nearest shelter, I am in Namkhana)*

**Say:**
> "The SOS is queued in an outbox, it sends the instant any network returns. It also
> found the nearest cyclone shelter from an offline registry, and it keeps a family
> check-in board for reunification."

*(Optional family board line: type `বাবা নিরাপদ আছে` "father is safe" and point to the
FAMILY BOARD card updating.)*

## Shot 4: Photo triage (1:25 to 1:50)

**Do:** Tap the 📷 button, attach the medicine strip photo, then type or say:
> `এই ওষুধ কী? মেয়াদ আছে?`  *(what medicine is this, is it in date?)*

**Note:** the first photo response can take about 30 to 60 seconds while the vision
model loads. Either wait quietly, or cut the gap in editing. If you warmed it during
setup, it is quick.

**Say:**
> "After a flood, people find soaked, unreadable medicine strips. I show Gemma 4 a
> photo, it reads the label and tells me, in plain Bengali, what it is and whether it
> is expired. Vision, reading, and translation in one offline step."

## Shot 5: Close (1:50 to 2:00)

**Say:**
> "One open model, Gemma 4, doing Bengali voice, vision, grounded first aid, and
> function calling, fully offline on a normal laptop. Every other assistant fails the
> moment the network dies. Ours is built for exactly that moment. When the network
> dies, help shouldn't. That is SAHAY."

**Screen:** end on the home screen with the sidebar showing Network DEAD (red) and
Gemma 4 ALIVE (amber).

## Tips

- If a response is slow, cut the dead air in editing; do not wait on camera.
- Keep the Wi-Fi-off moment; it is the whole pitch.
- Add one caption at the start: "Wi-Fi is OFF for this entire demo."
- If you leave the app idle for a long time before a take, send one throwaway message
  to re-warm the model first.
- Export as MP4 and upload to YouTube (unlisted is fine). Kaggle requires a YouTube
  link for the writeup's video.
