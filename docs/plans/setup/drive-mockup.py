import os
import sys
import tempfile
from playwright.sync_api import sync_playwright
html = open(sys.argv[1]).read()
# screenshots go to the second argument, or a temporary folder.
OUT = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix="bt-mockup-")
src = "<!doctype html><html><head><meta charset='utf-8'></head><body>" + html + "</body></html>"
Q = "() => { const l=[...document.querySelectorAll('#screen .ln')].map(x=>x.textContent); const i=l.map(x=>x.startsWith('◆')).lastIndexOf(true); return i<0?null:l[i] }"
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    for sc in ["first", "mate", "cluster", "upgrade"]:
        p = b.new_page(viewport={"width": 1400, "height": 1100}); errs = []
        p.on("pageerror", lambda e: errs.append(str(e))); p.on("console", lambda m: m.type == "error" and errs.append(m.text))
        p.set_content(src); p.click(f"[data-sc={sc}]"); p.click("#term")
        seen = []
        for _ in range(30):
            p.wait_for_timeout(3500 if not seen else 2500)
            if p.evaluate("() => document.querySelector('#screen').textContent.includes('$ ▍') || /is set up/.test(document.querySelector('#screen').textContent)"):
                seen.append("DONE"); break
            t = p.evaluate(Q)
            if t is None: continue
            t = t.strip()[:70]
            if seen and seen[-1] == t: seen.append("STUCK"); break
            seen.append(t)
            if sc == "first" and "is the record" in t:
                p.keyboard.press("ArrowDown"); p.wait_for_timeout(150); p.screenshot(path=os.path.join(OUT, f"rules-runs.png"), full_page=False)
                p.keyboard.press("ArrowUp"); p.wait_for_timeout(150); p.locator("#term").screenshot(path=os.path.join(OUT, f"rules-record.png"))
            if sc == "first" and "past work" in t:
                p.keyboard.press("+"); p.wait_for_timeout(200); p.keyboard.type("~/research/egnn-2024/beamtime"); p.keyboard.press("Enter"); p.wait_for_timeout(1500)
                p.locator("#term").screenshot(path=os.path.join(OUT, f"import.png"))
            if sc == "upgrade" and "Ready" in t:
                p.locator("#term").screenshot(path=os.path.join(OUT, f"upgrade-review.png"))
            p.keyboard.press("Enter")
        if sc in ("first", "upgrade"): p.locator("#term").screenshot(path=os.path.join(OUT, f"done-{sc}.png"))
        print(sc, "->", " | ".join(seen)); print("   cmd:", p.text_content("#n-cmd").replace("\n", " ")); print("   errors:", errs)
    b.close()
    print("screenshots:", OUT)
