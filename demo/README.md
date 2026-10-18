# Demo assets

- `CivicLens_Working_Prototype_Demo.mp4`: narrated 3–4 minute capture of actual app interactions.
- `capture.py`: reproducible capture workflow. From the project folder, install `requirements.txt`, run `playwright install ffmpeg`, then run `python demo/capture.py` on macOS with Google Chrome installed. Set `CHROME_PATH` for another Chromium executable. The script starts a fresh local app server, drives real browser interactions, records WebM, generates spoken narration with macOS `say`, and muxes the narrated MP4. It deliberately disables Gemini and Firestore so the visible classification mode is local rules and the 50→5 seed state is reproducible. It requires working loopback browser access and internet for Esri map tiles.
- `CivicLens_Working_Prototype_Raw.webm`: silent raw browser recording for audit or re-editing.
Exact recorded narration is in `capture.py`. The older slide preview and its render intermediates are excluded from this folder.

When capturing a genuine demonstration, clearly distinguish fallback classification from verified Gemini output and do not show secrets.
