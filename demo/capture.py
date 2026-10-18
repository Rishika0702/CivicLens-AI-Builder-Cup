"""Record the running CivicLens app and narrate its actual interactions.

Run from the project root: python demo/capture.py
Uses a fresh in-memory server, so the visible 50-to-5 seed state is reproducible.
No API credentials are used or stored by this script.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'demo'
PORT = 8766
URL = f'http://127.0.0.1:{PORT}'
OUTPUT = DEMO / 'CivicLens_Working_Prototype_Demo.mp4'
CHROME = os.getenv('CHROME_PATH') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# Each line describes the screen state at the given second in the recording.
NARRATION = [
 (2, 'This is CivicLens, a running civic complaint prototype for Hyderabad. The figures on screen are seeded synthetic data: fifty citizen reports grouped into five actionable incidents.'),
 (21, 'The map shows five live incident markers over real geographic map tiles. I am opening a marker now. Each marker summarizes nearby reports in the same issue category, rather than treating every report as a separate job.'),
 (43, 'The municipal priority queue ranks those incidents using urgency and report count. The first pothole incident has ten reports and urgency five. This is an interactive dashboard, with the list generated from the application API.'),
 (63, 'Now I am using the citizen complaint form. This demonstration uses typed text and the local rules classifier. Gemini is not configured with a fresh key in this environment, so no live Gemini result is claimed.'),
 (80, 'I am entering a dangerous pothole report at Jubilee Hills Junction. Its coordinates match an existing pothole cluster, which lets us verify duplicate grouping after submission.'),
 (99, 'I submit the complaint through the live form. The FastAPI backend classifies the issue as a pothole, assigns urgency, stores the report in memory, and checks for a nearby incident in the same category.'),
 (119, 'The response shows a new report identifier linked to incident zero zero one, with a visible local fallback provider label. The report has merged into that existing incident.'),
 (140, 'Back on the overview, the count is now fifty one complaints, still five incidents, and forty six merged duplicates. The change comes from the actual API response, not an edited graphic.'),
 (161, 'The map marker can be opened again to inspect the updated cluster. The incident now represents eleven citizen reports. The map tiles, markers, and popup are part of the running application.'),
 (182, 'The priority queue also updates to eleven reports for this incident. CivicLens is a prototype: records reset on restart, while optional Gemini and Firestore integrations need fresh credentials and separate verification before production use.'),
]

def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)

def wait_for_server():
    for _ in range(100):
        try:
            data = httpx.get(URL + '/health', timeout=1).json()
            if data['status'] == 'ok':
                return data
        except Exception:
            pass
        time.sleep(.1)
    raise RuntimeError('Local CivicLens server did not start')

def capture(raw):
    env = {**os.environ, 'GEMINI_API_KEY': '', 'FIRESTORE_ENABLED': 'false'}
    server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app',
                               '--host', '127.0.0.1', '--port', str(PORT)],
                              cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
    try:
        health = wait_for_server()
        assert not health['gemini_configured'] and health['mode'] == 'demo-memory'
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME, headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 900},
                                          device_scale_factor=1,
                                          record_video_dir=str(raw.parent),
                                          record_video_size={'width': 1440, 'height': 900})
            page = context.new_page()
            page.goto(URL, wait_until='domcontentloaded', timeout=30000)
            page.locator('#reports').get_by_text('50').wait_for(timeout=15000)
            page.locator('#mode').get_by_text('LOCAL RULES CLASSIFIER', exact=False).wait_for()
            page.locator('#map .leaflet-tile-loaded').first.wait_for(timeout=20000)
            started = time.monotonic()
            def at(seconds):
                remaining = seconds - (time.monotonic() - started)
                if remaining > 0:
                    page.wait_for_timeout(int(remaining * 1000))
            at(18)
            page.locator('nav a[href="#map-section"]').click()
            at(25)
            page.locator('#map .leaflet-interactive').first.click()
            page.locator('.leaflet-popup-content').wait_for()
            at(39)
            page.locator('nav a[href="#incidents-section"]').click()
            at(59)
            page.locator('nav a[href="#report-section"]').click()
            at(77)
            page.locator('#description').fill('A dangerous pothole near Jubilee Hills Junction is causing accidents and urgent road damage')
            at(92)
            page.locator('#lat').fill('17.4318')
            page.locator('#lng').fill('78.4071')
            at(96)
            page.locator('#submit').click()
            page.locator('#result').get_by_text('REP-0051', exact=False).wait_for(timeout=15000)
            result = page.locator('#result').inner_text()
            assert 'INC-001' in result and 'merged with existing incident' in result and 'fallback' in result
            at(135)
            page.locator('nav a[href="#overview"]').click()
            page.locator('#reports').get_by_text('51').wait_for()
            assert page.locator('#incidents').inner_text() == '5'
            assert page.locator('#merged').inner_text() == '46'
            at(157)
            page.locator('nav a[href="#map-section"]').click()
            at(164)
            page.locator('#map .leaflet-interactive').first.click()
            at(178)
            page.locator('nav a[href="#incidents-section"]').click()
            at(199)
            page.locator('nav a[href="#overview"]').click()
            at(207)
            video_path = page.video.path()
            context.close()
            browser.close()
            shutil.move(video_path, raw)
            print('Recorded genuine app interactions:', raw)
    finally:
        server.terminate()
        server.wait(timeout=10)

def narrate_and_mux(raw):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory(prefix='civiclens-audio-') as temp:
        audio_files = []
        for i, (_, line) in enumerate(NARRATION):
            path = Path(temp) / f'voice-{i:02}.aiff'
            run(['say', '-v', os.getenv('CIVICLENS_VOICE', 'Samantha'), '-r', '157', '-o', str(path), line])
            audio_files.append(path)
        inputs = [arg for path in audio_files for arg in ('-i', str(path))]
        delays = [f'[{i}:a]adelay={int(start*1000)}:all=1[a{i}]'
                  for i, (start, _) in enumerate(NARRATION)]
        mixed = ''.join(f'[a{i}]' for i in range(len(audio_files)))
        filter_graph = ';'.join(delays + [f'{mixed}amix=inputs={len(audio_files)}:duration=longest:normalize=0,aresample=async=1[aout]'])
        audio = Path(temp) / 'narration.m4a'
        run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *inputs,
             '-filter_complex', filter_graph, '-map', '[aout]', '-c:a', 'aac', '-b:a', '160k', str(audio)])
        run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(raw), '-i', str(audio),
             '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
             '-pix_fmt', 'yuv420p', '-af', 'apad', '-c:a', 'aac', '-b:a', '160k',
             '-shortest', '-movflags', '+faststart', str(OUTPUT)])
    print('Narrated MP4:', OUTPUT)

if __name__ == '__main__':
    DEMO.mkdir(exist_ok=True)
    raw = DEMO / 'CivicLens_Working_Prototype_Raw.webm'
    capture(raw)
    narrate_and_mux(raw)
