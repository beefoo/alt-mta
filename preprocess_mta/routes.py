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
    "Station ID": "id",
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
    routeStations = sorted(routeStations, key=lambda k: k['id'])

    # break up the route by lines
    lines = {}
    for station in routeStations:
        line = station["lineLabel"]
        if line not in lines:
            lines[line] = [station]
        else:
            lines[line].append(station)

    lineKeys = [line for line in lines]
    print "%s route has %s lines" % (route, len(lineKeys))

    if len(lineKeys) > 1:
        lineData = []
        for line in lines:
            lineData.append({
                "id": line,
                "stations": lines[line],
                "first": lines[line][0],
                "last": lines[line][-1],
                "isFirst": False,
                "connectsTo": False
            })

        # Find the first line:
        # assume the line with the first station farthest from all the last stations is the first station
        for i, line in enumerate(lineData):
            distancesToOtherLines = [
                {
                    "id": l["id"],
                    "distance": distance((l["last"]["lon"], l["last"]["lat"]), (line["first"]["lon"], line["first"]["lat"]))
                } for l in lineData if l["id"] != line["id"]
            ]
            distancesToOtherLines = sorted(distancesToOtherLines, key=lambda k: k['distance'], reverse=True)
            lineData[i]["distance"] = distancesToOtherLines[0]
        lineData = sorted(lineData, key=lambda k: k['distance'], reverse=True)
        lineData[0]["isFirst"] = True
        # print "The first station: %s" % lineData[0]["first"]["label"]

        # Connect the lines together, starting with the first line
        sortedLines = [lineData.pop(0)]
        currentLastStation = sortedLines[0]["last"]
        while len(lineData) > 0:
            # find the first station closest to the currentLast station
            distancesToOtherLines = [
                {
                    "index": i,
                    "id": l["id"],
                    "last": l["last"],
                    "distance": distance((currentLastStation["lon"], currentLastStation["lat"]), (l["first"]["lon"], l["first"]["lat"]))
                } for i, l in enumerate(lineData)
            ]
            distancesToOtherLines = sorted(distancesToOtherLines, key=lambda k: k['distance'])
            closestLine = distancesToOtherLines[0]
            sortedLines[-1]["connectsTo"] = closestLine["id"]
            currentLastStation = closestLine["last"]
            sortedLines.append(lineData.pop(closestLine["index"]))

        # Now sort the route
        sortedRouteStations = []
        for line in sortedLines:
            sortedRouteStations += line["stations"]
        routeStations = sortedRouteStations[:]

    d["stations"] = routeStations
    routeData.append(d)

jsonOut = routeData

# Write to file
with open(args.OUTPUT_FILE, 'w') as f:
    json.dump(jsonOut, f)
    print "Wrote %s items to %s" % (len(routes), args.OUTPUT_FILE)
