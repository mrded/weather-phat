#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
#import json
import time
import urllib
import argparse
from inky import InkyPHAT
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne

try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

print("""Inky pHAT: Weather

Displays weather information for a given location. The default location is Yeovil.

""")

# Command line arguments to set display colour

parser = argparse.ArgumentParser()
parser.add_argument('--colour', '-c', type=str, required=True, choices=["red", "black", "yellow"], help="ePaper display colour")
args = parser.parse_args()

# Set up the display

colour = args.colour
inky_display = InkyPHAT(colour)
inky_display.set_border(inky_display.BLACK)

# Details to customise your weather display

CITY = "Yeovil"
COUNTRYCODE = "GB"
WARNING_TEMP = 25.0

# Query the OpenWeatherMap weather API to get current weather data
def get_weather(address):
    base = "http://api.openweathermap.org/data/2.5/weather?q="
    units = "units=metric"
    api = ""

    uri= base + address + "&" + units + "&appid=" + api

    res = requests.get(uri).json()
    return res


def create_mask(source, mask=(inky_display.WHITE, inky_display.BLACK, inky_display.RED)):
    """Create a transparency mask.

    Takes a paletized source image and converts it into a mask
    permitting all the colours supported by Inky pHAT (0, 1, 2)
    or an optional list of allowed colours.

    :param mask: Optional list of Inky pHAT colours to allow.

    """
    mask_image = Image.new("1", source.size)
    w, h = source.size
    for x in range(w):
        for y in range(h):
            p = source.getpixel((x, y))
            if p in mask:
                mask_image.putpixel((x, y), 255)

    return mask_image


# Dictionaries to store our icons and icon masks in
icons = {}
masks = {}

# Get the weather data for the given location
location_string = "{city},{countrycode}".format(city=CITY, countrycode=COUNTRYCODE)
weather = get_weather(location_string)

# This maps the weather codes from the Yahoo weather API
# to the appropriate weather icons
icon_map = {
    "snow": [600, 601, 602, 611, 612, 613, 615, 616, 620, 621, 622],
    "rain": [500, 501, 502, 503, 504, 511, 520, 521, 522, 531],
    "drizzle": [300, 301, 302, 310, 311, 312, 313, 314, 321],
    "cloud": [801, 802, 803, 804],
    "sun": [800],
    "storm": [200, 201, 202, 210, 211, 212, 221, 230, 231, 232],
    "wind": [701, 711, 721, 731, 741, 751, 761, 762, 771, 781]
}

# Placeholder variables
pressure = 0
temperature = 0
weather_icon = None

# Pull out the appropriate values from the weather data
pressure = weather["main"]["pressure"]
temperature = weather["main"]["temp"]
code = weather["weather"][0]["id"]

for icon in icon_map:
    if code in icon_map[icon]:
        weather_icon = icon
        break

# Create a new canvas to draw on
img = Image.open("resources/backdrop.png")
draw = ImageDraw.Draw(img)

# Load our icon files and generate masks
for icon in glob.glob("resources/icon-*.png"):
    icon_name = icon.split("icon-")[1].replace(".png", "")
    icon_image = Image.open(icon)
    icons[icon_name] = icon_image
    masks[icon_name] = create_mask(icon_image)

# Load the FredokaOne font
font = ImageFont.truetype(FredokaOne, 22)

# Draw lines to frame the weather data
draw.line((69, 36, 69, 81))       # Vertical line
draw.line((31, 35, 184, 35))      # Horizontal top line
draw.line((69, 58, 174, 58))      # Horizontal middle line
draw.line((169, 58, 169, 58), 2)  # Red seaweed pixel :D

# Write text with weather values to the canvas
datetime = time.strftime("%d/%m %H:%M")

draw.text((36, 12), datetime, inky_display.WHITE, font=font)

draw.text((72, 34), "T", inky_display.WHITE, font=font)
draw.text((92, 34), u"{:.2f}°".format(temperature), inky_display.WHITE if temperature < WARNING_TEMP else inky_display.RED, font=font)

draw.text((72, 58), "P", inky_display.WHITE, font=font)
draw.text((92, 58), "{}".format(pressure), inky_display.WHITE, font=font)

# Draw the current weather icon over the backdrop
if weather_icon is not None:
    img.paste(icons[weather_icon], (28, 36), masks[weather_icon])

else:
    draw.text((28, 36), "?", inky_display.RED, font=font)

# Display the weather data on Inky pHAT
inky_display.set_image(img)
inky_display.show()
