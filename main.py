from flask import Flask, redirect, abort
from pyproj import Proj, transform
from antiquities import find_map_by_coordinates
from static_maps import static_maps

app = Flask(__name__)

# Define the ITM projection (EPSG:2039)
itm = Proj("epsg:2039")

# Define the WGS84 Latitude/Longitude projection
wgs84 = Proj("epsg:4326")


def decimal_to_dms(deg):
    """Convert decimal degrees to degrees, minutes, and seconds tuple."""
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    s = (md - m) * 60
    return (d, m, s)


def convert_coordinates(x, y, coord_type):
    """Convert coordinates based on the type specified."""
    match coord_type:
        case "dms":
            # Convert from decimal degrees to degrees, minutes, seconds
            lat_dms = decimal_to_dms(y)
            lon_dms = decimal_to_dms(x)
            return (
                f"{lat_dms[0]}°{lat_dms[1]}'{lat_dms[2]:.3f}\"N",
                f"{lon_dms[0]}°{lon_dms[1]}'{lon_dms[2]:.3f}\"E",
            )
        case "itm":
            # Convert from WGS84 to Israel Transverse Mercator
            easting, northing = transform(wgs84, itm, x, y)
            return easting, northing
        case _:
            return x, y


@app.route(
    "/redirect/<float(signed=True):x>/<float(signed=True):y>/<coord_type>/<path:target>",
    methods=["GET"],
)
def redirect_with_coords(x, y, coord_type, target):
    """Redirect to a specified URL with converted coordinates."""
    converted_x, converted_y = convert_coordinates(x, y, coord_type)
    # Construct the target URL with query parameters
    target_url = target.format(x=converted_x, y=converted_y)
    return redirect(target_url)


@app.route(
    "/iaa_survey/<float(signed=True):x>/<float(signed=True):y>", methods=["GET"]
)
def iaa_open_map(x, y):
    relevant_map = find_map_by_coordinates(static_maps, x, y)
    if not relevant_map:
        abort(404)
    return redirect(
        f"https://survey.antiquities.org.il/#/MapSurvey/{relevant_map['id']}/Zoom/15/Center/{x}&{y}"
    )


@app.route(
    "/govmap/<float(signed=True):x>/<float(signed=True):y>", methods=["GET"]
)
def govmap(x, y):
    zoom = 11
    layers = [
        "ATIKOT_SITES_ITM",
        "YESHUVIM_ET_ATIKA",
    ]  # Interesting layers from the site
    layers_string = ",".join(layers)
    (converted_x, converted_y) = convert_coordinates(x, y, "itm")
    # A URL which is both centered at the point and showing relevant layer information about the point:
    return redirect(
        f"https://www.govmap.gov.il/?c={converted_x},{converted_y}&z={zoom}&b=2&lay={layers_string}&bs={layers_string}%7C{converted_x},{converted_y}"
    )


if __name__ == "__main__":
    app.run(debug=True)
