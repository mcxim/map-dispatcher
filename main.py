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
        "https://survey.antiquities.org.il/#/MapSurvey/{map_id}/Zoom/15/Center/{x}&{y}".format(
            map_id=relevant_map["id"],
            x=x,
            y=y
        )
    )


if __name__ == "__main__":
    app.run(debug=True)
