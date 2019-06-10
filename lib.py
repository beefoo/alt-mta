# -*- coding: utf-8 -*-

import colorsys
import csv
import json
import math
import os

def distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

def distance3(p0, p1):
    x = p1[0] - p0[0]
    y = p1[1] - p0[1]
    z = p1[2] - p0[2]
    return math.sqrt(x**2 + y**2 + z**2)

def hex2hsv(hex):
    r, g, b = hex2rgb(hex)
    return colorsys.rgb_to_hsv(r, g, b)

def hex2rgb(hex):
    h = hex.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2 ,4))

def parseHeadings(arr, headings):
    newArr = []
    headingKeys = [key for key in headings]
    for i, item in enumerate(arr):
        newItem = {}
        for key in item:
            if key in headingKeys:
                newItem[headings[key]] = item[key]
        newArr.append(newItem)
    return newArr

def parseNumber(string):
    try:
        num = float(string)
        if "." not in string:
            num = int(string)
        return num
    except ValueError:
        return string

def parseNumbers(arr):
    for i, item in enumerate(arr):
        for key in item:
            arr[i][key] = parseNumber(item[key])
    return arr

def parseRouteData(fn, ufn):
    # read data
    routes = []
    with open(fn) as f:
        routes = json.load(f)

    uroutes = {}
    with open(ufn) as f:
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

    return routes

def radiansBetweenPoints(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    deltaX = x2 - x1;
    deltaY = y2 - y1;
    return math.atan2(deltaY, deltaX)

def readCsv(filename, headings, doParseNumbers=True):
    rows = []
    if os.path.isfile(filename):
        with open(filename, 'r', encoding="utf8") as f:
            lines = [line for line in f if not line.startswith("#")]
            reader = csv.DictReader(lines, skipinitialspace=True)
            rows = list(reader)
            rows = parseHeadings(rows, headings)
            if doParseNumbers:
                rows = parseNumbers(rows)
    return rows

def translatePoint(p, radians, distance):
    x, y = p
    x2 = x + distance * math.cos(radians)
    y2 = y + distance * math.sin(radians)
    return (x2, y2)
