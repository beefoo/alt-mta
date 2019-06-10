# -*- coding: utf-8 -*-

import argparse
from bs4 import BeautifulSoup
import json
from lib import *
import math
import os
from pprint import pprint
import re
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="usergen/subway_map.svg", help="SVG input file")
parser.add_argument('-data', dest="ROUTE_DATA", default="output/routes.json", help="Route data file")
parser.add_argument('-udata', dest="UROUTE_DATA", default="usergen/routes.json", help="User generated route data file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/subway_map_clean.svg", help="SVG output file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just output info?")
a = parser.parse_args()

routes = parseRouteData(a.ROUTE_DATA, a.UROUTE_DATA)

# Parse the svg like html
soup = None
with open(a.INPUT_FILE) as f:
    soup = BeautifulSoup(f, 'html.parser')

print("=====")

# Look for problematic symbols
symbolEls = soup.find_all(id=re.compile("symbol\-[0-9]+\_.*"))
if len(symbolEls) > 0:
    print("Found %s symbols in non-standard format; fixing:" % len(symbolEls))
    for symbol in symbolEls:
        id = symbol.get("id")
        symbol["id"] = id.split("_")[0]
        print(" - %s -> %s" % (id, symbol["id"]))

def normalizeText(string):
    nstring = string.lower()
    nstring = re.sub('[^0-9a-zA-Z ]+', ' ', nstring)
    nstring = ' '.join(nstring.split()) # remove mulitple whitespace
    # HACK: hardcode some problematic ones
    nstring = nstring.replace('b way', 'broadway')
    nstring = nstring.replace('n conduit', 'north conduit')
    return nstring

# Process text
textEl = soup.find(id="texts")
stationsProcessed = []
for route in routes:
    routeId = route["id"]
    routeTextEl = textEl.find(id="text-%s" % routeId, recursive=False)
    print("-----")

    # rename
    if routeTextEl:
        routeTextEl["id"] = "texts-%s" % routeId
    else:
        routeTextEl = textEl.find(id="texts-%s" % routeId, recursive=False)
    if not routeTextEl:
        print("Could not find texts group %s" % routeId)
        continue

    # wrap text elements in groups
    textEls = routeTextEl.find_all("text", id=re.compile("text\-[0-9]+"), recursive=False)
    if len(textEls) > 0:
        print("Route %s text was not transformed; wrapping in groups" % routeId)
        for el in textEls:
            newGroup = soup.new_tag("g")
            newGroup["id"] = el["id"]
            del el["id"]
            el.wrap(newGroup)

    # look for text that has been expanded to separate text els
    else:
        textEls = routeTextEl.find_all("text", recursive=False)
        if len(textEls) > 0:
            print("Route %s text has been expanded; wrapping in groups" % routeId)

        currentTextGroup = []
        currentString = ""
        currentLines = []
        textGroups = []
        pendingClose = False
        for el in textEls:
            elStr = el.string.strip()
            if len(elStr)==1 or "•" in elStr.encode("utf-8"):
                currentTextGroup.append(el)
                pendingClose = True
            else:
                if pendingClose:
                    pendingClose = False
                    textGroups.append({
                        "els": currentTextGroup[:],
                        "text": normalizeText(currentString),
                        "lines": currentLines[:]
                    })
                    currentTextGroup = []
                    currentLines = []
                    currentString = ""
                currentString += " " + elStr
                currentLines.append(normalizeText(elStr))
                currentTextGroup.append(el)
        if pendingClose:
            textGroups.append({
                "els": currentTextGroup[:],
                "text": normalizeText(currentString),
                "lines": currentLines[:]
            })

        # Create a lookup for station ids based on label
        stationIds = {}
        stationLabels = []

        for group in route["groups"]:
            for station in group:
                stationLabel = normalizeText(station["label"])
                stationIds[stationLabel] = station["id"]
                stationLabels.append(stationLabel)

        stationLabelsMatched = []
        for group in textGroups:
            foundStationId = None
            if group["text"] not in stationIds:
                for label in stationLabels:
                    if group["text"] in label or label in group["text"] and label not in stationLabelsMatched:
                        print(" Matched %s -> %s" % (group["text"], label))
                        foundStationId = stationIds[label]
                        stationLabelsMatched.append(label)
                        break

            else:
                foundStationId = stationIds[group["text"]]
                stationLabelsMatched.append(group["text"])

            if not foundStationId:
                for label in stationLabels:
                    for line in group["lines"]:
                        if line in label or label in line and label not in stationLabelsMatched:
                            print(" Matched %s -> %s" % (group["text"], label))
                            foundStationId = stationIds[label]
                            stationLabelsMatched.append(label)
                            break

            if not foundStationId:
                print(" *** Could not find %s in route %s..." % (group["text"], routeId))
                sys.exit()

            # wrap the group's elements in a new group
            newGroup = soup.new_tag("g")
            newGroup["id"] = "text-%s" % foundStationId
            for i, el in enumerate(group["els"]):
                if i < 1:
                    el.wrap(newGroup)
                else:
                    newGroup.append(el.extract())

        # pprint(textGroups)
        # sys.exit()

if a.PROBE:
    sys.exit()

# Write HTML file
outputStr = soup.prettify()
with open(a.OUTPUT_FILE, "wb") as f:
    f.write(outputStr.encode('utf-8'))
