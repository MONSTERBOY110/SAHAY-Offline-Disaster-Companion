/* SAHAY frontend: voice + camera + chat against the local Gemma 4 backend. */

const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const composerEl = document.getElementById("composer");
const sendBtn = document.getElementById("btn-send");
const micBtn = document.getElementById("btn-mic");
const photoBtn = document.getElementById("btn-photo");
const fileInput = document.getElementById("file-input");
const imgPreview = document.getElementById("img-preview");
const toolChipTpl = document.getElementById("tpl-tool-chip");

let history = [];
let pendingImageB64 = null;
let mediaRecorder = null;
let audioChunks = [];
let busy = false;

/* ---------------------------------------------------------------- status */
async function refreshStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    const net = document.getElementById("net-readout");
    const netState = document.getElementById("net-state");
    if (s.online) {
      net.dataset.state = "up";
      netState.textContent = "ONLINE";
    } else {
      net.dataset.state = "down";
      netState.textContent = "DEAD";
    }
    document.getElementById("gemma-state").textContent =
      s.model_ready ? "ALIVE · LOCAL" : "LOADING…";
  } catch {
    const net = document.getElementById("net-readout");
    if (net) net.dataset.state = "down";
  }
}
refreshStatus();
setInterval(refreshStatus, 5000);

/* ------------------------------------------------------------- rendering */
const USER_AV = '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="3.4" stroke="currentColor" stroke-width="1.7"/><path d="M5 20a7 7 0 0 1 14 0" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';

function addMsg(role, html, opts = {}) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const av = document.createElement("span");
  av.setAttribute("aria-hidden", "true");
  if (role === "user") { av.className = "avatar av-user"; av.innerHTML = USER_AV; }
  else { av.className = "avatar av-sahay"; av.textContent = "স"; }
  wrap.appendChild(av);
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.lang = "bn";
  if (opts.photoSrc) {
    const img = document.createElement("img");
    img.src = opts.photoSrc;
    img.alt = "attached photo";
    img.className = "sent-photo";
    bubble.appendChild(img);
  }
  const content = document.createElement("div");
  content.innerHTML = html;
  bubble.appendChild(content);

  const col = document.createElement("div");
  col.className = "msg-col";
  col.appendChild(bubble);
  if (opts.transcript) {
    const t = document.createElement("p");
    t.className = "transcript-tag";
    t.textContent = `🎤 ${opts.transcript}`;
    col.appendChild(t);
  }
  wrap.appendChild(col);
  chatEl.appendChild(wrap);
  scrollDown();
  return wrap;
}

function addToolChip(ev) {
  const chip = toolChipTpl.content.cloneNode(true);
  const argStr = JSON.stringify(ev.args);
  chip.querySelector(".tool-code").textContent =
    `${ev.tool}(${argStr.length > 88 ? argStr.slice(0, 88) + "…" : argStr})`;
  chatEl.appendChild(chip);
  scrollDown();
}

function addTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg sahay typing";
  wrap.innerHTML =
    '<span class="avatar av-sahay" aria-hidden="true">স</span>' +
    '<div class="bubble"><i></i><i></i><i></i></div>';
  chatEl.appendChild(wrap);
  scrollDown();
  return wrap;
}

function scrollDown() {
  chatEl.scrollTo({ top: chatEl.scrollHeight, behavior: "smooth" });
}

/* Minimal safe markdown: bold, ordered/unordered lists, paragraphs. */
function md(text) {
  const esc = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const lines = esc.split(/\r?\n/);
  let html = "", inList = false;
  for (const line of lines) {
    const m = line.match(/^\s*(?:[-*]|\d+[.)])\s+(.*)/);
    if (m) {
      if (!inList) { html += "<ol>"; inList = true; }
      html += `<li>${m[1]}</li>`;
    } else {
      if (inList) { html += "</ol>"; inList = false; }
      if (line.trim()) html += `<p>${line}</p>`;
    }
  }
  if (inList) html += "</ol>";
  return html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

/* ------------------------------------------------------------------ send */
async function send({ text = "", audioB64 = null } = {}) {
  if (busy) return;
  const message = text.trim();
  if (!message && !audioB64 && !pendingImageB64) return;

  busy = true;
  sendBtn.disabled = true;

  const shownText = message || (audioB64 ? "🎤 (voice message)" : "📷 (photo)");
  addMsg("user", md(shownText), {
    photoSrc: pendingImageB64 ? `data:image/jpeg;base64,${pendingImageB64}` : null,
  });

  const payload = { message, image_b64: pendingImageB64, audio_b64: audioB64, history };
  pendingImageB64 = null;
  imgPreview.classList.add("hidden");
  photoBtn.classList.remove("has-photo");
  inputEl.value = "";
  autosize();

  const typing = addTyping();
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await r.json();
    typing.remove();

    for (const ev of data.tool_events || []) addToolChip(ev);
    addMsg("sahay", md(data.reply || "…"), { transcript: data.transcript });

    const userTurn = data.transcript
      ? `${message} ${data.transcript}`.trim()
      : (message || "(photo shared)");
    history.push({ role: "user", content: userTurn });
    history.push({ role: "assistant", content: data.reply || "" });
    if (history.length > 12) history = history.slice(-12);

    refreshRail();
  } catch {
    typing.remove();
    addMsg("sahay", md("**সংযোগে সমস্যা।** Backend unreachable, retry in a moment.\n" +
      "Check that the SAHAY server and Ollama are running."));
  } finally {
    busy = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

composerEl.addEventListener("submit", (e) => {
  e.preventDefault();
  send({ text: inputEl.value });
});
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    composerEl.requestSubmit();
  }
});
document.getElementById("quick-row").addEventListener("click", (e) => {
  const chip = e.target.closest(".chip");
  if (chip) send({ text: chip.dataset.q });
});

/* textarea autosize */
function autosize() {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 132) + "px";
}
inputEl.addEventListener("input", autosize);

/* ----------------------------------------------------------------- photo */
photoBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    pendingImageB64 = reader.result.split(",")[1];
    imgPreview.src = reader.result;
    imgPreview.classList.remove("hidden");
    photoBtn.classList.add("has-photo");
  };
  reader.readAsDataURL(file);
  fileInput.value = "";
});

/* ----------------------------------------------------------------- voice */
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      if (blob.size < 2000) return;
      send({ text: inputEl.value, audioB64: await blobToB64(blob) });
    };
    mediaRecorder.start();
    micBtn.classList.add("recording");
  } catch {
    addMsg("sahay", md("মাইক্রোফোন পাওয়া যায়নি। Microphone unavailable, please type instead."));
  }
}
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
  micBtn.classList.remove("recording");
}
function blobToB64(blob) {
  return new Promise((res) => {
    const r = new FileReader();
    r.onload = () => res(r.result.split(",")[1]);
    r.readAsDataURL(blob);
  });
}
micBtn.addEventListener("mousedown", startRecording);
micBtn.addEventListener("mouseup", stopRecording);
micBtn.addEventListener("mouseleave", stopRecording);
micBtn.addEventListener("touchstart", (e) => { e.preventDefault(); startRecording(); });
micBtn.addEventListener("touchend", (e) => { e.preventDefault(); stopRecording(); });

/* ------------------------------------------------------------ right rail */
async function refreshRail() {
  try {
    const [ob, fam] = await Promise.all([
      fetch("/api/outbox").then((r) => r.json()),
      fetch("/api/family").then((r) => r.json()),
    ]);
    renderOutbox(ob.outbox || []);
    renderFamily(fam.family || []);
  } catch { /* keep last state */ }
}

function renderOutbox(items) {
  const el = document.getElementById("outbox-list");
  if (!items.length) return;
  el.innerHTML = "";
  for (const s of items.slice().reverse()) {
    const d = document.createElement("div");
    d.className = "sos-item";
    d.innerHTML =
      `<div class="sos-to">→ ${s.to}</div>` +
      `<div class="sos-body">${s.body}</div>` +
      `<div class="sos-state">QUEUED · sends when network returns</div>`;
    el.appendChild(d);
  }
}

function renderFamily(items) {
  const el = document.getElementById("family-list");
  if (!items.length) return;
  el.innerHTML = "";
  for (const f of items) {
    const d = document.createElement("div");
    d.className = "family-item";
    d.innerHTML =
      `<div><div class="family-name">${f.name}</div>` +
      `<div class="family-loc">${f.location || ""}</div></div>` +
      `<span class="family-status ${f.status}">${f.status}</span>`;
    el.appendChild(d);
  }
}

/* shelter cards render from find_nearest_shelter tool events */
const _addToolChip = addToolChip;
addToolChip = function (ev) {
  _addToolChip(ev);
  if (ev.tool === "find_nearest_shelter" && ev.result && ev.result.shelters) {
    renderShelters(ev.result.shelters);
  }
};

function renderShelters(shelters) {
  const el = document.getElementById("shelter-list");
  el.innerHTML = "";
  for (const s of shelters) {
    const d = document.createElement("div");
    d.className = "shelter-item";
    d.innerHTML =
      `<div class="shelter-name">${s.name}</div>` +
      `<div class="shelter-name-bn" lang="bn">${s.name_bn || ""}</div>` +
      `<div class="shelter-meta">${s.area}, ${s.district}` +
      (s.landmark ? ` · ${s.landmark}` : "") +
      (s.capacity ? ` · capacity ~${s.capacity}` : "") + `</div>` +
      `<div class="shelter-fac">${(s.facilities || []).join(" · ")}</div>`;
    el.appendChild(d);
  }
}

refreshRail();
inputEl.focus();
