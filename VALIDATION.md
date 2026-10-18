# Validation — 18 October 2026

## Working prototype demo

- Started the FastAPI app locally and opened it in headless Google Chrome through Playwright. The page showed 50 seeded synthetic complaints, 5 incidents, 45 merged duplicates, and a visible `LOCAL RULES CLASSIFIER · DEMO MODE` label.
- Replaced the map tile source after the former provider returned `API KEY REQUIRED`. Confirmed the Esri tiles loaded in the actual browser.
- Recorded real app interactions: clicked a map marker, inspected the priority queue, typed and submitted a pothole complaint at Jubilee Hills Junction, saw `REP-0051 → INC-001` with `fallback` and a duplicate merge, then saw 51 complaints, 5 incidents, 46 merged duplicates, and 11 reports in the updated pothole cluster.
- Produced `demo/CivicLens_Working_Prototype_Demo.mp4` with synchronized spoken narration. Media inspection: **3:27.20**, H.264 video at **1440×900 / 25 fps**, AAC mono audio at **22,050 Hz**. Audio volume detection found mean **−18.2 dB** and peak **−1.6 dB**; sampled frames at the opening, map, queue, form, submission result, updated counts, and closing state.
- The unedited Playwright browser capture is retained as `demo/CivicLens_Working_Prototype_Raw.webm`. `demo/capture.py` reproduces the full capture and narration on a compatible macOS machine.

## App checks

- `pytest -q`: **5 passed**.
- Browser test confirmed the live page returned 50 reports, displayed the local classifier mode, showed five queue items, and loaded map tiles.
- Scanned code and documentation for common API-key patterns; no previously exposed key was included. `.env.example` contains empty placeholders.

## Limits

- This run did **not** use Gemini. Classification was the explicit local deterministic fallback. Fresh Gemini credentials and live integration verification remain necessary before claiming live AI classification.
- The 50→5 starting state is seeded synthetic data. The video demonstrates one additional real submission merging into an existing incident; it does not claim that 50 individual reports were entered during recording.
- Firestore and Cloud Run were not deployed or remotely verified. Records are kept in memory and reset on restart.
- The clean delivery folder contains the nine-slide revised pitch deck and the genuine prototype recording; the older slide preview is excluded.

## Pitch deck

- Slide 10 was removed. Slide 6 was corrected to describe the local classifier, Esri map tiles, the 700 m category merge, and optional cloud integrations.
- The nine-slide PPTX passed package integrity, layout, font, and re-import checks. All nine slides were rendered for visual review.
