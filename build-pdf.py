#!/usr/bin/env python3
"""Render jack-barry-cv.html to a one-page, full-colour A4 PDF.

Google Fonts are downloaded once and inlined as data URIs so the PDF embeds
the real typefaces instead of falling back to a system serif.

Usage: python3 build-pdf.py [path/to/chrome]
"""
import base64, os, re, subprocess, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "jack-barry-cv.html")
OUT = os.path.join(HERE, "jack-barry-cv.pdf")
CSS_URL = ("https://fonts.googleapis.com/css2?family=Archivo:wght@500;600"
           "&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")
CHROME_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA})).read()


def inline_fonts():
    """Return @font-face rules for the latin subsets, with fonts embedded."""
    css = fetch(CSS_URL).decode()
    rules = []
    for subset, block in re.findall(r"/\*\s*(\S+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S):
        if subset != "latin":
            continue
        fam = re.search(r"font-family: '([^']+)'", block).group(1)
        weight = re.search(r"font-weight: (\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        rng = re.search(r"unicode-range: ([^;]+);", block).group(1)
        data = base64.b64encode(fetch(url)).decode()
        rules.append(
            f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{weight};"
            f"font-stretch:100%;src:url(data:font/woff2;base64,{data}) format('woff2');"
            f"unicode-range:{rng};}}")
    return "\n".join(rules)


def find_chrome():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for path in CHROME_CANDIDATES:
        if os.path.isfile(path):
            return path
    sys.exit("Chrome/Chromium not found - pass the path as an argument.")


def main():
    html = open(SRC).read()
    body = "\n".join(l for l in html.split("\n") if "fonts.g" not in l)
    body = body.replace("<style>", "<style>\n" + inline_fonts() + "\n", 1)
    page = ('<!doctype html><html><head><meta charset="utf-8">'
            + body.replace('<div class="sheet">', '</head><body><div class="sheet">', 1)
            + "</body></html>")

    with tempfile.TemporaryDirectory() as tmp:
        render = os.path.join(tmp, "render.html")
        open(render, "w").write(page)
        subprocess.run([find_chrome(), "--headless", "--disable-gpu", "--no-sandbox",
                        "--no-pdf-header-footer", "--virtual-time-budget=8000",
                        f"--print-to-pdf={OUT}", "file://" + render],
                       check=True, capture_output=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
