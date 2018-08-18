# -*- coding: utf-8 -*-

# python symbols.py -symbol data/symbol_dot_express.png

# Image source: http://web.mta.info/maps/images/subway_map_Jul18_2700x3314.jpg
# Template matching: https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_template_matching/py_template_matching.html

import argparse
import cv2
import json
import math
import numpy as np
import os
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_IMAGE", default="data/subway_map_Jul18_2700x3314.jpg", help="Path to input image")
parser.add_argument('-dir', dest="INPUT_SYMBOL_DIR", default="data/", help="Path to input symbol directory")
parser.add_argument('-threshold', dest="THRESHOLD", default=0.75, type=float, help="Matching threshold")
parser.add_argument('-mout', dest="OUTPUT_IMAGE", default="output/symbols.png", help="JSON output file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/symbols.json", help="JSON output file")

args = parser.parse_args()

SYMBOLS = [
    {"image": "symbol_dot_local.png"},
    {"image": "symbol_dot_express.png", "express": True},
    {"image": "symbol_dot_express_hub.png", "hub": True, "express": True},
    {"image": "symbol_dot_express_hub2.png", "hub": True, "express": True},
    {"image": "symbol_pill_express_hub2.png", "hub": True, "express": True, "threshold": 0.8},
    {"image": "symbol_pill_express_hub1.png", "hub": True, "express": True, "threshold": 0.8},
    {"image": "symbol_dot_local_sir.png", "threshold": 0.798},
    {"image": "symbol_dot_local_closed.png", "threshold": 0.95},
    {"image": "symbol_dot_local_custom1.png", "threshold": 0.95},
    {"image": "symbol_pill_express_hub_custom1.png", "hub": True, "express": True, "threshold": 0.95},
    {"image": "symbol_pill_express_hub_custom2.png", "hub": True, "express": True, "threshold": 0.95},
    {"image": "symbol_pill_express_hub_custom3.png", "hub": True, "express": True, "threshold": 0.95},
    {"image": "symbol_pill_express_hub_custom4.png", "hub": True, "express": True, "threshold": 0.95},
    {"image": "symbol_pill_express_hub_custom5.png", "hub": True, "express": True, "threshold": 0.95},
    {"image": "symbol_pill_express_hub_custom6.png", "hub": True, "express": True, "threshold": 0.95},
    {"image": "symbol_pill_local_hub_custom1.png", "hub": True, "threshold": 0.95}
]

# Parse symbols
symbols = SYMBOLS[:]
for i, symbol in enumerate(symbols):
    symbols[i]["path"] = args.INPUT_SYMBOL_DIR + symbol["image"]
    symbols[i]["meta"] = {
        "express": (1 if "express" in symbol else 0),
        "hub": (1 if "hub" in symbol else 0)
    }

# Read source image
img_rgb = cv2.imread(args.INPUT_IMAGE)
img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

# Find each symbol
symbolsData = []
for i, symbol in enumerate(symbols):
    template = cv2.imread(symbol["path"], 0)
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = args.THRESHOLD
    if "threshold" in symbol:
        threshold = symbol["threshold"]
    loc = np.where(res >= threshold)
    matches = zip(*loc[::-1])
    for m in matches:
        cx = m[0] + w * 0.5
        cy = m[1] + h * 0.5
        exists = False
        # Check if center exists in a previous match
        for sd in symbolsData:
            p = sd["point"]
            s = sd["size"]
            if p[0] < cx < p[0]+s[0] and p[1] < cy < p[1]+s[1]:
                exists = True
                break
        if not exists:
            d = symbol["meta"].copy()
            d.update({
                "point": [int(m[0]), int(m[1])],
                "size": [int(w), int(h)]
            })
            symbolsData.append(d)
    print "Found %s symbols for %s" % (len(matches), symbol["path"])

# write image for debugging
for symbol in symbolsData:
    pt = symbol["point"]
    sz = symbol["size"]
    cv2.rectangle(img_rgb, tuple(pt), (pt[0] + sz[0], pt[1] + sz[1]), (0,0,255), 1)
cv2.imwrite(args.OUTPUT_IMAGE, img_rgb)
print "Wrote matches to %s" % args.OUTPUT_IMAGE

jsonOut = symbolsData[:]

# Write to file
with open(args.OUTPUT_FILE, 'w') as f:
    json.dump(jsonOut, f)
    print "Wrote %s items to %s" % (len(symbolsData), args.OUTPUT_FILE)
