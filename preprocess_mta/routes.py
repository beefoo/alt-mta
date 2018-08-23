# -*- coding: utf-8 -*-

# Data sources: http://web.mta.info/developers/developer-data-terms.html#data
    # Stations: http://web.mta.info/developers/data/nyct/subway/Stations.csv
    # Colors: http://web.mta.info/developers/data/colors.csv

import argparse
import collections
import json
from lib import *
import math
import os
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-stations', dest="STATIONS_FILE", default="data/Stations.csv", help="Stations input file")
parser.add_argument('-routes', dest="ROUTES_FILE", default="data/Routes.csv", help="Routes input file")
parser.add_argument('-colors', dest="COLORS_FILE", default="data/colors.csv", help="Colors input file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/routes.json", help="JSON output file")

args = parser.parse_args()

stationHeadings = {
    "Station ID": "id",
    "Line": "lineLabel",
    "Stop Name": "label",
    "Borough": "borough",
    "Daytime Routes": "routes",
    "Structure": "structure",
    "GTFS Latitude": "lat",
    "GTFS Longitude": "lon",

}
routeHeadings = {
    "Station ID": "stationId",
    "Sort By": "sortBy",
    "Route": "route",
    "Group": "groups"
}
colorHeadings = {
    "Line/Branch": "lines",
    "RGB Hex Map": "hex"
}

# Retrieve data
stationData = readCsv(args.STATIONS_FILE, stationHeadings)
routeOrderData = readCsv(args.ROUTES_FILE, routeHeadings)
colorData = readCsv(args.COLORS_FILE, colorHeadings, doParseNumbers=False)

# Parse routes
for i, station in enumerate(stationData):
    stationData[i]["id"] = str(station["id"])
    stationData[i]["routes"] = str(station["routes"]).split(" ")
for i, route in enumerate(routeOrderData):
    routeOrderData[i]["route"] = str(route["route"])
    routeOrderData[i]["stationId"] = str(route["stationId"])
    if len(route["groups"]) > 0:
        routeOrderData[i]["groups"] = str(route["groups"]).split(" ")
    else:
        routeOrderData[i]["groups"] = []


# get list of unique groups
groups = [r["groups"] for r in routeOrderData]
groups = [item for sublist in groups for item in sublist]
groups = list(set(groups))
print ("Found %s groups" % len(groups))
pprint(groups)

# Check for duplicates
ids = [s["id"] for s in stationData]
duplicates = [item for item, count in collections.Counter(ids).items() if count > 1]
if len(duplicates) > 0:
    print("Warning: %s duplicates found." % len(duplicates))
    pprint(duplicates)

# Parse colors
for i, color in enumerate(colorData):
    delimeter = "/"
    if delimeter not in color["lines"]:
        delimeter = " "
    colorData[i]["lines"] = color["lines"].split(delimeter)
    colorData[i]["hex"] = "#" + color["hex"]

routes = [s["routes"] for s in stationData]

# Flatten routes
routes = [route for sublist in routes for route in sublist]
routes = list(set(routes))

routeData = []

for route in routes:
    d = { "id": route }

    # order the stations via route config
    routeOrder = [s for s in routeOrderData if s["route"]==route]
    routeOrder = dict(zip([r["stationId"] for r in routeOrder], [r for r in routeOrder]))

    routeStations = [s for s in stationData if route in s["routes"]]
    rgroups = []
    for i, s in enumerate(routeStations):
        r = routeOrder[s["id"]]
        routeStations[i]["sortBy"] = r["sortBy"]
        if len(r["groups"]) > 0:
            routeStations[i]["groups"] = r["groups"]
            rgroups += r["groups"]
    routeStations = sorted(routeStations, key=lambda k: k['sortBy'])

    # add groups to route
    rgroups = list(set(rgroups))
    if len(rgroups) > 0:
        d["groups"] = rgroups

    d["stations"] = routeStations
    routeData.append(d)

# Add color to routes
for i, route in enumerate(routeData):
    colors = [c for c in colorData if route["id"] in c["lines"]]
    if len(colors) <= 0:
        print "No color found for %s" % route["id"]
    else:
        routeData[i]["color"] = colors[0]["hex"]

jsonOut = routeData

# Write to file
with open(args.OUTPUT_FILE, 'w') as f:
    json.dump(jsonOut, f)
    print "Wrote %s items to %s" % (len(routes), args.OUTPUT_FILE)
