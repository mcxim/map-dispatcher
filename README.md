# Map Dispatcher

Deployed at: https://mcxim.pythonanywhere.com/

## Problem

The obsidian map view plugin has an option to add custom "open in" actions, but only by templating the WGS84 coordinates as `{x}` and `{y}` in the URL. Some use cases require more functionality.

## Solution

Running the extra logic on a server that computes the final URL and redirects there.

## Features

### WGS84 -> ITM Conversion

Converting from WGS84 coordinates to Israeli Transverse Mercator for sites like Amud Anan.

The URL I configured in obsidian map view: http://mcxim.pythonanywhere.com/redirect/{x}/{y}/itm/http%3A%2F%2Famudanan.co.il%2F%23lat%3D%7By%7D%26lon%3D%7Bx%7D

### Israel Antiquities Authority Surveys

There are a lot of surveys and you first have to resolve the survey which corresponds to your specific location. Then, you can zoom into the specific place inside the map.

I didn't find any automatic coordinates -> survey id conversion, so I wrote it myself.

The URL I configured in obsidian map view: http://mcxim.pythonanywhere.com/iaa_survey/{x}/{y}
