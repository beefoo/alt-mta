# -*- coding: utf-8 -*-

# Data source: http://web.mta.info/developers/data/nyct/subway/Stations.csv
    # Via: http://web.mta.info/developers/developer-data-terms.html#data

import argparse
import json
from lib import *
import math
import os
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/Stations.csv", help="Forcings input file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="routes.json", help="JSON output file")

args = parser.parse_args()

headings = {
    "GTFS Stop ID": "id",
    "Line": "lineLabel",
    "Stop Name": "label",
    "Borough": "borough",
    "Daytime Routes": "routes",
    "Structure": "structure",
    "GTFS Latitude": "lat",
    "GTFS Longitude": "lon"
}

# Retrieve data
stationData = readCsv(args.INPUT_FILE, headings)

# Parse routes
for i, station in enumerate(stationData):
    stationData[i]["id"] = str(station["id"])
    stationData[i]["routes"] = str(station["routes"]).split(" ")

routes = [s["routes"] for s in stationData]

# Flatten routes
routes = [route for sublist in routes for route in sublist]
routes = list(set(routes))

routeData = []

for route in routes:
    d = { "id": route }
    routeStations = [s for s in stationData if route in s["routes"]]
    d["stations"] = sorted(routeStations, key=lambda k: k['id'])
    routeData.append(d)

jsonOut = routeData

# Write to file
with open(args.OUTPUT_FILE, 'w') as f:
    json.dump(jsonOut, f)
    print "Wrote %s items to %s" % (len(routes), args.OUTPUT_FILE)
