import subprocess
import os
import sys

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome_path):
    print("Chrome not found at", chrome_path)
    sys.exit(1)

out_png = r"d:\PricePulse BD\chrome_trend_modal.png"
out_dom = r"d:\PricePulse BD\chrome_trend_dom.html"

# Run chrome headless screenshot of 30-day trend modal
cmd_screen = [
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--virtual-time-budget=5000",
    f"--screenshot={out_png}",
    "--window-size=1280,1050",
    "http://127.0.0.1:8000/#basket-trend"
]

res = subprocess.run(cmd_screen, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=25)
print("Trend Modal Screenshot exit code:", res.returncode)
print("Trend Modal PNG exists:", os.path.exists(out_png), "Size:", os.path.getsize(out_png) if os.path.exists(out_png) else 0)

# Run chrome headless dump-dom
cmd_dom = [
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--virtual-time-budget=5000",
    "--dump-dom",
    "http://127.0.0.1:8000/#basket-trend"
]
res_dom = subprocess.run(cmd_dom, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
print("DOM exit code:", res_dom.returncode)
with open(out_dom, "w", encoding="utf-8") as f:
    f.write(res_dom.stdout or "")
print("DOM written. Size:", len(res_dom.stdout or ""), "bytes")
