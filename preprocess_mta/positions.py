# -*- coding: utf-8 -*-

import argparse
from cllib import *
import json
from lib import *
import math
import os
from PIL import Image
import numpy as np
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="INPUT_DATA", default="output/routes.json", help="Path to input data")
parser.add_argument('-image', dest="INPUT_IMAGE", default="data/subway_map_Jul18_2700x3314.jpg", help="Path to input image")
parser.add_argument('-out', dest="OUTPUT_IMAGE", default="debug/subway_map_posterized.jpg", help="Image output file")
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
stationData = []
with open(args.INPUT_DATA) as f:
    stationData = json.load(f)

# retrieve colors
colors = list(set([s["color"] for s in stationData]))
colorLen = len(colors)
# convert to rgb
colors = [hex2rgb(c) for c in colors]
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

__kernel void posterize(__global uchar *px, __global uchar *colors, __global uchar *result){
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
    float threshold = 10.0;

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
""" % (w, dim, colorLen)

# build program
ctx, prg, queue = buildProgram(src)

# buffer input and execute program
inPx = getInBuffer(ctx, px)
inColors = getInBuffer(ctx, colors)
outResult = getOutBuffer(ctx, px.nbytes)
prg.posterize(queue, [h, w], None , inPx, inColors, outResult)

# Copy result
result = np.empty_like(px)
copyResult(queue, result, outResult)

# Convert back to original shape
result = result.reshape(shape)

# Write new image
im = Image.fromarray(result, mode="RGB")
im.save(args.OUTPUT_IMAGE)
print "Saved image to %s" % args.OUTPUT_IMAGE
