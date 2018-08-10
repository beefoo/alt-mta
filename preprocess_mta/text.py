# -*- coding: utf-8 -*-

import argparse
from PIL import Image
import json
import math
from pprint import pprint
import pyocr
import pyocr.builders
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_IMAGE", default="data/subway_map_Jul18_2700x3314.jpg", help="Path to input image")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/text.json", help="JSON output file")
args = parser.parse_args()

tools = pyocr.get_available_tools()
if len(tools) == 0:
    print("No OCR tool found")
    sys.exit(1)
tool = tools[0]
print("Will use tool '%s'" % (tool.get_name()))

langs = tool.get_available_languages()
print("Available languages: %s" % ", ".join(langs))
lang = langs[0]
print("Will use lang '%s'" % (lang))

print("Finding line boxes...")
builder = pyocr.builders.LineBoxBuilder()
lineBoxes = tool.image_to_string(
    Image.open(args.INPUT_IMAGE),
    lang=lang,
    builder=builder
)

# Remove empty boxes
lineBoxes = [lb for lb in lineBoxes if len(lb.content) > 0]
print("Found %s boxes" % (len(lineBoxes)))

for lb in lineBoxes[:20]:
    pprint(lb.content)
    pprint(lb.position)
