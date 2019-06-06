# -*- coding: utf-8 -*-

import argparse
import json
from lib import *
import math
import os
from PIL import Image
from pprint import pprint
import svgwrite as svg
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="ROUTE_DATA", default="output/routes.json", help="Route data file")
parser.add_argument('-udata', dest="UROUTE_DATA", default="usergen/routes.json", help="User generated route data file")
parser.add_argument('-map', dest="MAP_IMAGE", default="data/subway_map_Jul18_2700x3314.jpg", help="Map image for reference")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/routes.svg", help="SVG output file")
# map style options
parser.add_argument('-linew', dest="LINE_WIDTH", default=5, type=int, help="Line stroke width")
parser.add_argument('-linec', dest="LINE_CURVINESS", default=0.3, type=float, help="Bigger number is more curvy; probably between 0.1 and 0.5")
parser.add_argument('-symbolw', dest="SYMBOL_LINE_WIDTH", default=2, type=int, help="Line stroke width for symbols")
parser.add_argument('-fontsize', dest="FONT_SIZE", default=14, type=int, help="Font size")
a = parser.parse_args()

# open the map image
im = Image.open(a.MAP_IMAGE)
width, height = im.size
print("Target size: %s x %s" % (width, height))

# read data
routes = []
with open(a.ROUTE_DATA) as f:
    routes = json.load(f)

uroutes = {}
with open(a.UROUTE_DATA) as f:
    uroutes = json.load(f)

# add uroutes to routes
for i, route in enumerate(routes):
    id = route["id"]
    if id not in uroutes:
        continue
    uroute = uroutes[id]
    for j, station in enumerate(route["stations"]):
        sid = station["id"]
        if sid not in uroute["stations"]:
            continue
        ustation = uroute["stations"][sid]
        routes[i]["stations"][j].update(ustation)

    stations = routes[i]["stations"]
    groups = [[s.copy() for s in stations]]
    # check if we have groups that we need to break up
    if "groups" in route and len(route["groups"]) > 0:
        groups = []
        for group in route["groups"]:
            gstations = [s.copy() for s in stations if "groups" in s and group in s["groups"]]
            groups.append(gstations)
    routes[i]["groups"] = groups

dwg = svg.Drawing(a.OUTPUT_FILE, size=(width, height), profile='full')

# add guides
guides = dwg.add(dwg.g(id="guides"))
guides.add(dwg.image(href=os.path.basename(a.MAP_IMAGE), insert=(0,0), size=(width, height)))

# add center points
for i, route in enumerate(routes):
    for j, group in enumerate(route["groups"]):
        for k, station in enumerate(group):
            x, y = tuple(station["point"])
            w, h = tuple(station["size"])
            x += w*0.5
            y += h*0.5
            routes[i]["groups"][j][k]["cpoint"] = (x, y)

# add control points to stations
for i, route in enumerate(routes):
    for j, group in enumerate(route["groups"]):
        scount = len(group)
        for k, station in enumerate(group):
            p = station["cpoint"]
            p0 = p2 = cp0 = cp2 = False
            if k > 0:
                p0 = group[k-1]["cpoint"]
            if k < scount-1:
                p2 = group[k+1]["cpoint"]
            # middle
            if p0 and p2:
                radians = radiansBetweenPoints(p2, p0)
                pd = min(distance(p2, p0), distance(p, p0), distance(p2, p)) * a.LINE_CURVINESS
                cp0 = translatePoint(p, radians, pd)
                cp2 = translatePoint(p, radians, -pd)
            # first point
            elif p2:
                radians = radiansBetweenPoints(p2, p)
                pd = distance(p2, p) * a.LINE_CURVINESS
                cp2 = translatePoint(p, radians, -pd)
            # last point
            elif p0:
                radians = radiansBetweenPoints(p, p0)
                pd = distance(p, p0) * a.LINE_CURVINESS
                cp0 = translatePoint(p, radians, pd)
            routes[i]["groups"][j][k]["controlPoints"] = (cp0, cp2)

# add lines
lines = dwg.add(dwg.g(id="lines", stroke_width=a.LINE_WIDTH, stroke_linecap="round", fill="none"))
for route in routes:
    rlines = lines.add(dwg.g(id="lines-%s" % route["id"], stroke=route["color"]))
    for group in route["groups"]:
        d = []
        for k, station in enumerate(group):
            x, y = station["cpoint"]
            if k <= 0:
                d.append("M%s %s" % (x, y))
            else:
                prev = group[k-1]
                cp0 = prev["controlPoints"][1]
                cp2 = station["controlPoints"][0]
                # if not cp2:
                #     pprint(station)
                x0, y0 = cp0
                x2, y2 = cp2
                x0 = round(x0, 2)
                y0 = round(y0, 2)
                x2 = round(x2, 2)
                y2 = round(y2, 2)
                # use shorthand if possible
                if k > 1:
                    d.append("S%s,%s %s,%s" % (x2, y2, x, y))
                else:
                    d.append("C%s,%s %s,%s %s,%s" % (x0, y0, x2, y2, x, y))
        rlines.add(dwg.path(id="line-%s" % station["id"], d=d))

# add symbols
symbols = dwg.add(dwg.g(id="symbols", stroke="#000000", stroke_width=a.SYMBOL_LINE_WIDTH, fill="#ffffff"))
stationsDrawn = []
for route in routes:
    rsymbols = symbols.add(dwg.g(id="symbols-%s" % route["id"]))
    for group in route["groups"]:
        for station in group:
            if station["id"] in stationsDrawn:
                continue
            x, y = tuple(station["point"])
            cx, cy = station["cpoint"]
            w, h = tuple(station["size"])
            radius = min(w, h) * 0.5
            # draw a circle if dimensions are about the same
            if abs(w-h) <= 1:
                rsymbols.add(dwg.circle(id="symbol-%s" % station["id"], center=(cx, cy), r=radius))
            # otherwise draw a rectangle
            else:
                rsymbols.add(dwg.rect(id="symbol-%s" % station["id"], insert=(x, y), size=(w, h), rx=radius, ry=radius))
            stationsDrawn.append(station["id"])

# add text
texts = dwg.add(dwg.g(id="texts", font_size=a.FONT_SIZE))
stationsDrawn = []
for route in routes:
    rtexts = texts.add(dwg.g(id="text-%s" % route["id"]))
    for group in route["groups"]:
        for station in group:
            if station["id"] in stationsDrawn:
                continue
            cx, cy = station["cpoint"]
            textString = station["label"] + " " + "•".join(station["routes"])
            rtexts.add(dwg.text(textString, id="text-%s" % station["id"], insert=(cx, cy)))
            stationsDrawn.append(station["id"])

dwg.save()
print("Done.")
