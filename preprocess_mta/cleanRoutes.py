# -*- coding: utf-8 -*-

import argparse
import json
import math
import os
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="INPUT_DATA", default="output/routes.json", help="Path to input route data")
parser.add_argument('-udata', dest="INPUT_UDATA", default="usergen/routes.json", help="Path to input usergen route data")
args = parser.parse_args()

# retrieve data
routes = []
with open(args.INPUT_DATA) as f:
    routes = json.load(f)

uroutes = {}
with open(args.INPUT_UDATA) as f:
    uroutes = json.load(f)

changed = False
for route in routes:
    id = route["id"]
    if id not in uroutes:
        print("Warning: %s not found in uroutes" % id)
        continue
    uroute = uroutes[id]
    sids = [s["id"] for s in route["stations"]]
    usids = [uid for uid in uroute["stations"]]

    add = list(set(sids) - set(usids))
    subtract = list(set(usids) - set(sids))
    if len(add) <= 0 and len(subtract) <= 0:
        continue

    for sid in add:
        uroute["stations"][sid] = {}
        print("Added %s to %s" % (sid, id))

    for sid in subtract:
        uroute["stations"].pop(sid, None)
        print("Removed %s from %s" % (sid, id))

    uroutes[id] = uroute
    changed = True

if changed:
    # Write to file
    with open(args.INPUT_UDATA, 'w') as f:
        json.dump(uroutes, f)
        print("Updated %s" % args.INPUT_UDATA)
else:
    print("No change.")
