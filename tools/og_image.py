#!/usr/bin/env python3
"""Render og-image.png (1200x630), the picture LinkedIn/Slack show when the page link is shared.

    python3 tools/og_image.py        # needs Pillow
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda name, size: ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', name), size)
W, H = 1200, 630
BG, FG, MUTED, LINE = (10, 13, 21), (231, 235, 244), (144, 153, 174), (42, 51, 73)
BRANCH = [(59, 123, 255), (139, 92, 246), (14, 165, 198), (245, 158, 11), (244, 63, 94)]


def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.pi / 6 + i * math.pi / 3), cy + r * math.sin(math.pi / 6 + i * math.pi / 3)) for i in range(6)]


img = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(img)

# faint honeycomb of skill badges on the right, coloured by branch
for row in range(7):
    for col in range(6):
        cx, cy = 840 + col * 66 + (33 if row % 2 else 0), 70 + row * 57
        k = (row * 7 + col) % 5
        lit = (row + col * 3) % 4 != 0
        d.polygon(hexagon(cx, cy, 27), outline=BRANCH[k] if lit else LINE, width=2 if lit else 1)

# emblem
d.polygon(hexagon(110, 150, 46), outline=FG, width=3)
d.line([(82, 152), (96, 152), (102, 136), (110, 170), (118, 144), (124, 152), (138, 152)], fill=(14, 165, 198), width=4, joint='curve')

d.text((80, 250), 'Zbigniew Zabost', font=F('space-grotesk-var.woff2', 76), fill=FG)
d.text((82, 350), 'Senior Site Reliability Engineer', font=F('space-grotesk-var.woff2', 38), fill=FG)
d.text((82, 405), 'Kubernetes fleets on AWS, Azure & GCP', font=F('ibm-plex-mono-400.woff2', 26), fill=MUTED)
d.text((82, 442), 'delivery platforms · AI agents for operations', font=F('ibm-plex-mono-400.woff2', 26), fill=MUTED)
d.text((82, 540), '#SRE  #Kubernetes  #PlatformEngineering  #AIOps', font=F('ibm-plex-mono-500.woff2', 24), fill=BRANCH[3])

img.save(os.path.join(ROOT, 'og-image.png'), optimize=True)
print('og-image.png written')
