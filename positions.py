# -*- coding: utf-8 -*-

import argparse
from cllib import *
import json
from lib import *
import math
import os
from PIL import Image, ImageDraw
import numpy as np
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="INPUT_DATA", default="output/routes.json", help="Path to input route data")
parser.add_argument('-sym', dest="INPUT_SYMBOLS", default="output/symbols.json", help="Path to input symbols data")
parser.add_argument('-image', dest="INPUT_IMAGE", default="data/subway_map_Jul18_2700x3314.jpg", help="Path to input image")
parser.add_argument('-thres', dest="COLOR_THRESHOLD", type=float, default=10.0, help="The max 3D RGB distance to match color")
parser.add_argument('-out', dest="OUTPUT_IMAGE", default="debug/color_matches.jpg", help="Image output file")
args = parser.parse_args()

os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

# open image
im = Image.open(args.INPUT_IMAGE)
px = np.array(im)
px = px.astype(np.uint8)
shape = px.shape
h, w, dim = shape
# one-dimensional array
px = px.reshape(-1)

# retrieve data
routes = []
with open(args.INPUT_DATA) as f:
    routes = json.load(f)
symbols = []
with open(args.INPUT_SYMBOLS) as f:
    symbols = json.load(f)

# retrieve colors
colors = list(set([r["color"] for r in routes]))
colorLen = len(colors)
# convert to rgb
colors = [hex2rgb(c) for c in colors]
routeColors = colors[:]
# convert to np array of ints
colors = np.array(colors)
colors = colors.astype(np.uint8)
colors = colors.reshape(-1)

# the kernel function
src = """
static float d3(int r1, int g1, int b1, int r2, int g2, int b2) {
    float r = (float) (r2 - r1);
    float g = (float) (g2 - g1);
    float b = (float) (b2 - b1);
    return sqrt(r*r + g*g + b*b);
}

__kernel void findColors(__global uchar *px, __global uchar *colors, __global uchar *result){
    int w = %d;
    int dim = %d;
    int colorLen = %d;

    // get the current pixel
    int posx = get_global_id(1);
    int posy = get_global_id(0);
    int i = posy * w * dim + posx * dim;
    int r = px[i];
    int g = px[i+1];
    int b = px[i+2];

    int outR = 255;
    int outG = 255;
    int outB = 255;
    float threshold = %f;

    for(int ci=0; ci<colorLen; ci++) {
        int j = ci * dim;
        int cr = colors[j];
        int cg = colors[j+1];
        int cb = colors[j+2];

        if (d3(r, g, b, cr, cg, cb) < threshold) {
            outR = r;
            outG = g;
            outB = b;
            break;
        }
    }

    result[i] = outR;
    result[i+1] = outG;
    result[i+2] = outB;
}
""" % (w, dim, colorLen, args.COLOR_THRESHOLD)

# build program
print "Building program..."
ctx, prg, queue = buildProgram(src)

# buffer input and execute program
print("Finding colors...")
inPx = getInBuffer(ctx, px)
inColors = getInBuffer(ctx, colors)
outResult = getOutBuffer(ctx, px.nbytes)
prg.findColors(queue, [h, w], None , inPx, inColors, outResult)

# Copy result
result = np.empty_like(px)
copyResult(queue, result, outResult)

# Convert back to original shape
result = result.reshape(shape)

# Convert to image
im = Image.fromarray(result, mode="RGB")
draw = ImageDraw.Draw(im)

print("Matching colors to symbols...")
MATCH_THRESHOLD = 10
SAMPLE_RADIUS = 5

# Look for symbols that have this color around it
for i, symbol in enumerate(symbols):
    sx, sy = tuple(symbol["point"])
    sw, sh = tuple(symbol["size"])

    # determine bounds
    x0 = max(sx - SAMPLE_RADIUS, 0)
    y0 = max(sy - SAMPLE_RADIUS, 0)
    x1 = min(sx + sw + SAMPLE_RADIUS, w)
    y1 = min(sy + sh + SAMPLE_RADIUS, h)

    colorMatches = []
    for color in routeColors:

        # loop through symbol's perimeter and look for color
        matches = 0
        for dy in range(y1-y0):
            for dx in range(x1-x0):
                y = dy + y0
                x = dx + x0
                 # don't include the space in the symbol itself
                if x < sx or y < sy or x >= sx+sw or y >= sy+sh:
                    c = result[y, x]
                    if distance3(color, c) < args.COLOR_THRESHOLD:
                        matches += 1

        # if we have enough color matches, we can say this symbol belongs to this route
        if matches >= MATCH_THRESHOLD:
            colorMatches.append(color)

    # draw color arcs
    if len(colorMatches) > 0:
        degreesPerColor = 360.0 / len(colorMatches)
        degreesFrom = 0.0
        for color in colorMatches:
            draw.arc([sx, sy, sx+sw, sy+sh], start=degreesFrom, end=(degreesFrom+degreesPerColor), fill=color)
            degreesFrom += degreesPerColor

    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*(i+1)/len(symbols)*100,1))
    sys.stdout.flush()

# Write new image
print("Writing image...")
im.save(args.OUTPUT_IMAGE)
print("Saved image to %s" % args.OUTPUT_IMAGE)
