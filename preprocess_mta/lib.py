# -*- coding: utf-8 -*-

import colorsys
import csv
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

def readCsv(filename, headings, doParseNumbers=True):
    rows = []
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            lines = [line for line in f if not line.startswith("#")]
            reader = csv.DictReader(lines, skipinitialspace=True)
            rows = list(reader)
            rows = parseHeadings(rows, headings)
            if doParseNumbers:
                rows = parseNumbers(rows)
    return rows
