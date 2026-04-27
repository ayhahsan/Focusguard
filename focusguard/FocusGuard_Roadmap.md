# FocusGuard — Complete Build Roadmap

**Project:** AI Focus Coach using Computer Vision
**Tagline:** Your AI focus trainer — privacy-first, runs 100% offline
**Target User:** Students, freelancers, knowledge workers, anyone who struggles to focus
**Timeline:** 4 weeks (focused work)
**Cost:** ₹0 — sab open-source

---

## 1. Project In One Line

Webcam pe AI silently watch karta hai → real-time bataye kab tum distracted ho (phone uthaya, idhar-udhar dekha, neend aa rhi) → focus score deta hai + end-of-day beautiful heatmap.

**Sab kuch offline. Tumhara webcam feed kabhi cloud nahi jayega.**

---

## 2. Kya Detect Karega — 6 Distraction Signals

| Signal | Kaise detect | Kyun matter karta hai |
|--------|--------------|----------------------|
| **Eye gaze direction** | MediaPipe iris tracking | Screen pe nahi dekh rhe = distracted |
| **Head pose** | Face mesh landmarks | Neeche dekh rhe (phone) = distracted |
| **Phone in hand** | YOLOv8-nano object detection | Direct phone usage signal |
| **Drowsiness** | Eye Aspect Ratio (EAR) algorithm | Aankh band/half-closed = neend |
| **Presence** | Face detection | User left desk |
| **Yawning** | Mouth Aspect Ratio (MAR) | Fatigue indicator |

In sab signals ko ek **Focus Score (0-100)** mein combine karenge — weighted aggregate, smoothed over time.

---

## 3. User Experience — Aaisa Dikhega

### Live Mode (working session ke time)
- Top-right corner mein chhoti floating pill: "Focus: 87"
- Score 60 ke neeche jaaye → gentle desktop notification: "Tum 5 min se distracted ho — 2-min break le?"
- Score 30 ke neeche → louder alert with "Refocus exercise" suggestion

### Dashboard (end of session)
- **Today's focus heatmap** — 9am-6pm horizontal timeline, color intensity = focus
- **Distraction breakdown** — pie chart: 40% phone, 25% gaze drift, 15% drowsy, 20% absent
- **Peak focus zones** — "Tumhara golden hour 10:30-11:45am tha"
- **Streaks** — "5 din se 4hr+ deep work — keep going!"

### Privacy Mode
- Big red "PRIVACY: WEBCAM FRAMES NEVER SAVED" banner
- Optional: blur preview so user knows AI is working but actual frame nahi store hota

---

## 4. Tech Stack (Sab Free)

| Layer | Tool | Kyun |
|-------|------|------|
| Face/eye/iris tracking | **MediaPipe** (Google) | Best free CV library, real-time on CPU |
| Object detection (phone) | **YOLOv8-nano** (Ultralytics) | Smallest, fastest variant |
| Camera | **OpenCV** | Standard webcam interface |
| Real-time loop | Pure Python | No frameworks needed |
| Dashboard | **Streamlit** | Beautiful UI in pure Python |
| Storage | **SQLite** | Local DB, zero setup |
| Notifications | **plyer** | Cross-platform desktop notifications |
| Charts | **Plotly** | Interactive, sexy visualizations |
| Packaging | **PyInstaller** | Single .exe / .app file |

**No GPU. No cloud. No API. Sab CPU pe smoothly chalega.**

---

## 5. Architecture

```
┌─────────────────────────────────────────────┐
│           FocusGuard Application            │
│                                             │
│  ┌────────────┐                             │
│  │  Webcam    │ → frames @ 15 FPS           │
│  └────────────┘                             │
│        ↓                                    │
│  ┌────────────────────────────────────────┐ │
│  │       Detection Pipeline               │ │
│  │  ┌──────────────────────────────────┐  │ │
│  │  │ MediaPipe Face Mesh              │  │ │
│  │  │  - Eye landmarks (gaze, EAR)     │  │ │
│  │  │  - Head pose (pitch/yaw/roll)    │  │ │
│  │  │  - Mouth (yawn detection)        │  │ │
│  │  └──────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────┐  │ │
│  │  │ YOLOv8-nano                      │  │ │
│  │  │  - Phone detection (every 2s)    │  │ │
│  │  └──────────────────────────────────┘  │ │
│  └────────────────────────────────────────┘ │
│        ↓                                    │
│  ┌────────────────────────────────────────┐ │
│  │      Focus Score Engine                │ │
│  │  - Weighted aggregate                  │ │
│  │  - Temporal smoothing (no jitter)      │ │
│  │  - Confidence + state tracking         │ │
│  └────────────────────────────────────────┘ │
│        ↓                                    │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │ Live Overlay │    │ SQLite Logger    │   │
│  └──────────────┘    └──────────────────┘   │
└─────────────────────────────────────────────┘
                                  ↓
                    ┌─────────────────────────┐
                    │   Streamlit Dashboard   │
                    │   (separate window)     │
                    └─────────────────────────┘
```

---

## 6. Week-By-Week Roadmap

### Week 1 — Foundation: Eye Tracking + Focus Score
**Goal:** Working CLI tool jo webcam dekh ke real-time focus score de

**Tasks:**
- [ ] Repo setup with proper structure
- [ ] OpenCV + MediaPipe integration
- [ ] Face detection — present/absent state
- [ ] Eye Aspect Ratio (EAR) for drowsiness
- [ ] Gaze direction estimation
- [ ] Head pose estimation
- [ ] Combine signals into focus score (0-100)
- [ ] Display score + visual feedback on webcam window
- [ ] Console logging of distraction events

**Deliverable:**
```bash
python focusguard.py
# Opens webcam, shows live focus score with overlay
# Press Q to quit, prints session summary
```

**This is what I will build for you in this message.**

---

### Week 2 — Phone Detection + Smart Alerts
**Tasks:**
- [ ] YOLOv8-nano integration (phone class only)
- [ ] Run object detection every 2s (not every frame — saves CPU)
- [ ] Mouth Aspect Ratio (yawning detection)
- [ ] Temporal smoothing — score should not jitter
- [ ] Distraction state machine (focused → drifting → distracted → absent)
- [ ] Desktop notifications via plyer
- [ ] Smart alert logic — don't spam, escalate gradually

**Deliverable:** Production-ready CLI with smart alerting

---

### Week 3 — SQLite Logger + Streamlit Dashboard
**Tasks:**
- [ ] SQLite schema: sessions, focus_events, distraction_events
- [ ] Background logger thread
- [ ] Streamlit dashboard with multi-page nav
- [ ] Today view: focus heatmap (hourly buckets)
- [ ] Trends view: 7-day, 30-day comparison
- [ ] Distraction breakdown pie + bar charts
- [ ] Peak focus hour insights
- [ ] Privacy panel — clear "no frames saved" indicator
- [ ] Export session data as CSV/JSON

**Deliverable:** Full app with dashboard — looks like a real product

---

### Week 4 — Polish, Demo, Launch
**Tasks:**
- [ ] PyInstaller build for Windows + Mac
- [ ] First-run setup wizard
- [ ] System tray integration (runs in background)
- [ ] Killer demo video (60-90 sec)
- [ ] GitHub README with GIFs
- [ ] Landing page (free GitHub Pages site)
- [ ] LinkedIn launch post + Twitter thread
- [ ] Submit to: Hacker News, Reddit r/productivity, Product Hunt, Awesome Self-Hosted

**Deliverable:** Public launch + first downloads

---

## 7. Killer Features Jo Stand Out Karenge

1. **100% Offline** — privacy story (matches Profiled brand)
2. **Adaptive Personalization** — learn user's baseline (some people naturally squint)
3. **Pomodoro Integration** — 25-min focus blocks with auto-detection
4. **Deep Work Heatmap** — Spotify Wrapped style end-of-week recap
5. **Calibration Mode** — first 60 sec calibrates to your face/setup
6. **Anti-Cheat Mode** — for students preparing exams, parents can verify focus session
7. **Twin Mode** — pair up with friend remotely, see each other's focus score (motivational)

Privacy + offline angle bahut strong sell point hai — others sab cloud-based hain.

---

## 8. Demo Strategy — Client Ko Kaise Impress Karein

### Demo Video Script (60-90 seconds)

**0:00-0:10 — Hook**
- Black screen text: "What if AI could watch you focus?"
- Webcam comes on, FocusGuard starts

**0:10-0:30 — Live demo**
- Tu coding kar rha hai → score 95
- Phone pick up karte ho → score drops to 40, alert pops up
- Yawning → score drops, "drowsiness detected"
- Look away → score drops

**0:30-0:60 — Dashboard reveal**
- End session click karte ho
- Beautiful dashboard transition
- Heatmap dikhao with insights
- "Your peak focus today: 10:30-11:45am"

**0:60-0:90 — Closer**
- "100% offline. No data leaves your machine."
- "Built with Python + MediaPipe — open source"
- GitHub link + your handle

### LinkedIn Post Template

> 80% of workers can't focus for a full hour. The average person gets distracted every 4 minutes.
>
> So I built **FocusGuard** — an AI focus coach that watches you, not your apps.
>
> Real-time focus tracking using computer vision:
> 👁️ Eye gaze direction
> 📱 Phone detection
> 😴 Drowsiness detection
> 🪑 Presence detection
>
> 100% offline. No webcam frames ever leave your machine.
> Built with Python, MediaPipe, and OpenCV.
>
> Demo video below ⬇️
>
> ⭐ GitHub: [link]
>
> #AI #ComputerVision #Productivity #OpenSource

---

## 9. Convert To Clients

### Path 1: Upwork Profile Update
- Title: "AI/ML Engineer | Computer Vision Specialist"
- Portfolio: Profiled (privacy) + FocusGuard (computer vision)
- Target gigs: "real-time computer vision", "MediaPipe developer", "attention tracking", "webcam ML"
- Rate jump: $30/hr → $50-70/hr with this portfolio

### Path 2: Niche Demand
With FocusGuard live, target these niches:
- **EdTech companies** — "I can add proctoring/attention tracking to your platform"
- **Productivity SaaS** — "Need real-time focus features?"
- **HR Tech** — Remote work monitoring (with consent)
- **Driver fatigue systems** — same EAR/drowsiness tech

### Path 3: Direct Outreach
LinkedIn message template:
> "Hi [name], I built FocusGuard — open-source real-time attention tracking using webcam + MediaPipe. I noticed [their company] does [related work]. Would a 30-min chat about how this could integrate into your stack be valuable? Demo: [link]"

### Path 4: Inbound (after launch)
Once GitHub stars cross 100, founders/PMs will DM you for:
- Custom integration work
- White-label versions
- Specific feature builds

---

## 10. Brand Story (Profiled + FocusGuard)

**Old bio:** "Aspiring AI/ML engineer"
**New bio:**
> 🔍 Privacy-first AI tools that actually run on your machine
> Building: Profiled (data exposure analyzer) · FocusGuard (focus coach)
> Open-source. Offline. Self-taught.

Ye narrative powerful hai — tu **"privacy-first AI engineer"** ban rha hai. Niche claim kar rha hai jismein abhi competition kam hai.

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| MediaPipe accuracy on dark skin | Test extensively, calibration mode |
| Privacy concerns from users | Aggressive "offline only" messaging |
| Webcam permission UX | One-time setup wizard with explainer |
| Battery/CPU drain | Adaptive frame rate (high when focused, low when idle) |
| Existing tools (RescueTime) | Tu BIOLOGICAL hai, wo APP-based — different category |
| Single-platform (initially Windows) | Cross-platform from day 1 (Python is portable) |

---

## 12. Success Metrics

**Week 4 launch ke baad:**
- 50+ GitHub stars (good)
- 200+ stars (excellent)
- 1+ blog post / podcast mention

**Month 2-3:**
- 500+ stars
- 1-2 paid consulting gigs
- Featured in 1 newsletter (TLDR, The Batch, Bytes)

**Month 6:**
- 1000+ stars
- Freelance pipeline established
- Possible product extension (mobile app, team version)

---

## 13. Next Step (Right Now)

Week 1 ka starter code main ek saath de raha hu — full working CLI demo. Tu bas:

1. Code download karo
2. `pip install -r requirements.txt`
3. `python focusguard.py`
4. Webcam on, live focus score dikhega

Fir Week 2 onwards khud build karna shuru kar — ya mujhe bolega toh next phase ka code bhi likh dunga.

**Aaja ab code banaate hain.**
