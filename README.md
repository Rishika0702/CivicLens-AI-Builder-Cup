# CivicLens — Every voice. One clearer city.

CivicLens is a **Google Cloud AI Builder Cup 2026** civic-tech prototype: citizens report city issues using text, images or browser speech recognition (English/Hindi/Telugu). A Gemini classifier (when configured) determines complaint type and urgency; geospatial/category deduplication consolidates reports into actionable incidents, displayed on a Leaflet map and municipal priority queue.

The narrated working-prototype capture is in `demo/CivicLens_Working_Prototype_Demo.mp4`.

## Start locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://127.0.0.1:8000
pytest -q
```

The default demo loads 50 synthetic reports into 5 category/location-based incidents. Without `GEMINI_API_KEY`, a deterministic **local rules classifier** is used and clearly indicated in UI and response. Speech input depends on browser speech-recognition support and network permissions; Esri map tiles need internet. Photo bytes are passed to Gemini when configured, but are not persistently stored.

## Enable Gemini safely

Export a newly rotated key in your shell, or use an untracked local `.env` loaded by your own environment manager. **Never commit the old shared keys.**

```bash
export GEMINI_API_KEY='NEW_ROTATED_SECRET'
uvicorn app.main:app --reload
```

Gemini response returns category, urgency, English summary, language, reason. API outage triggers explicit fallback instead of masquerading as AI output. For production, use Secret Manager.

## Firestore / Firebase integration

Set `FIRESTORE_ENABLED=true` and configure Application Default Credentials (`gcloud auth application-default login` locally, service account on Cloud Run). Writes to collections `reports` and `incidents`. Enable `REQUIRE_AUTH=true` for bearer-token verification of report submission; the frontend currently **does not implement a Firebase sign-in widget**, so enabling it requires adding a login/token flow. Municipal incident status updates are always token-gated. **Important:** the seeded demo is currently in-memory and not rehydrated from Firestore on restart; treat it as a proof-of-concept, not production persistence.

## Cloud Run deployment

1. Create/select a Google Cloud project with billing; enable Cloud Run, Cloud Build, Artifact Registry, Firestore and Secret Manager APIs; provision Firestore Native mode.
2. Create a fresh secret named `gemini-api-key`, give the Cloud Run runtime identity Secret Manager accessor, and ensure Firestore read/write permission.
3. Run `GOOGLE_CLOUD_PROJECT=... bash deploy/cloudrun.sh` from repository root. Review public-access settings before running; script deploys a publicly accessible demo.
4. Test `/health`, `/api/stats`, manual complaint creation, map, speech in browser, and permissions. Add application authentication before production.

## Core workflow

`Complaint (text/photo/browser voice) → Gemini classify/urgency (or transparent fallback) → same category within 700m → incident merge/new → score = 15 × max urgency + 1.7 × report count (capped at 50) → map + queue.`

Deduplication uses a category + geographic threshold heuristic, **not semantic embeddings**. This works for the supplied controlled demo but could incorrectly merge distinct incidents within 700m; a production version should use embeddings, road segment/landmark matching, human override and audit logs.

## APIs

- `GET /health` — running mode, Gemini configuration status
- `GET /api/stats` — total reports/incidents/duplicates/critical counts
- `GET /api/incidents` — prioritized incidents
- `GET /api/reports` — submitted reports
- `POST /api/reports` — text, coordinates, optional base64 photo
- `PATCH /api/incidents/{id}` — privileged incident status update (Firebase ID token required)

## What this prototype does **not** claim

No live municipality integration, service-level guarantees, municipal SSO, durable seed rehydration, actual incident verification, native audio upload or transcription server, ElevenLabs voice playback, production moderation, rate limiting, accessibility audit, or public URL. In the absence of keys, **Gemini is not running**. See `VALIDATION.md` for executed checks. Sample data is entirely synthetic.

## Submission assets

- `pitch/CivicLens_Pitch.pptx` — current nine-slide deck, with slide 10 removed and slide 6 corrected (the mandatory Hack2Skill template was unavailable for verification)
- `demo/CivicLens_Working_Prototype_Demo.mp4` — narrated capture of the running app, showing 50→5 seeded grouping, map, queue, report submission, local classification, and the resulting 51→5 state
- `demo/capture.py` — reproducible local capture and narration workflow
- `demo/CivicLens_Working_Prototype_Raw.webm` — unedited browser capture for audit or further editing
- `TECH_DESCRIPTION.md`, `SUBMISSION_CHECKLIST.md`, `VALIDATION.md`

## Security

Previously posted Gemini/ElevenLabs keys are exposed: **revoke/rotate** them. Use Google Secret Manager in Cloud Run, avoid embedding keys in browser JavaScript, git, slide notes, logs, or videos. Any authenticated deployment requires proper authorization checks and least privilege. This is not an official civic complaint service.
