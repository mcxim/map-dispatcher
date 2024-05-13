from functools import lru_cache
import requests
from urllib.parse import quote_plus
from pprint import pprint
from bs4 import BeautifulSoup
from dataclasses import dataclass
from static_maps import static_maps
from utils import partition

def quote_plus_underscore(str):
    return quote_plus(str).replace("_", "%5F")

@dataclass
class SiteInfo:
    name: str
    site_id: int
    link: str
    lat: float
    long: float
    photos: list[str]
    sketches: list[str]
    periods: list[str]
    remains: list[str]


OPEN_IN_MAP_URL_FORMAT = (
    "https://survey.antiquities.org.il/#/MapSurvey/{map_id}/site/{site_id}"
)
OPEN_IMAGE_URL_FORMAT = "https://survey.antiquities.org.il/{image_path}"
GET_MAPS_URL = (
    "https://survey.antiquities.org.il/aspxService/Service.aspx/GetMaps"
)
GET_SITES_URL_FORMAT = "https://survey.antiquities.org.il/aspxService/Service.aspx/GetSites?mapId={}"
GET_DESCRIPTION_URL_FORMAT = "https://survey.antiquities.org.il/aspxService/Service.aspx/GetSiteDesc2?Id={}"

BING_URL_FORMAT = "https://www.bing.com/maps?sp={markers}"
BING_MARKER_FORMAT = "point.{y}_{x}_{title}_{notes}_{link_url}_{photo}"


# Chrome web tools copy request as curl -> ChatGPT transform to python requests -> ChatGPT remove sensitive information like cookies etc:
headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-US,en;q=0.9,he;q=0.8,ru;q=0.7",
    "content-type": "application/json",
    "cookie": "redacted",
    "referer": "https://survey.antiquities.org.il/",
    "sec-ch-ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def is_mandate(info):
    return "המנדט הבריטי" in info.periods


def is_ottoman(info):
    return "העות'מאנית" in info.periods


def is_recent(info):
    return is_ottoman(info) or is_mandate(info)


def is_with_photos(info):
    return len([image for image in info.photos if "map" not in image]) > 0


def is_sketch(image_url):
    """
    The sketches contain "map" in their filename, while real photos don't.
    """
    return "map" in image_url


def find_map_by_coordinates(
    lat,
    long,
    delta_lat=0.05,  # 0.04510300056818182,  # From running some experiments on the data set using plt.hist and seeing the distribution
    delta_long=0.05,  # 0.05287043108333312,
    maps=static_maps,
):
    matches = []
    # Assuming a rectangular boundary around each center
    for map_entry in maps:
        center_lat = map_entry["LatSWNE"]
        center_long = map_entry["LongSWNE"]

        # Calculate boundaries assuming the center and a delta for latitude and longitude
        lat_sw = center_lat - delta_lat
        lat_ne = center_lat + delta_lat
        long_sw = center_long - delta_long
        long_ne = center_long + delta_long

        # Check if the provided lat/long is within the bounds
        if lat_sw <= lat <= lat_ne and long_sw <= long <= long_ne:
            matches.append(map_entry)

    match matches:
        case [first, *_]:
            return first
        case _:
            return None


def get_maps():
    # Check if the request was successful
    response = requests.get(GET_MAPS_URL, headers=headers)
    if response.status_code == 200:
        print("Request was successful.")
        maps_data = response.json()["d"]
    else:
        print(f"Failed to retrieve data: {response.status_code}")
    return maps_data


def get_sites(map_id):
    url = GET_SITES_URL_FORMAT.format(map_id)
    return requests.get(url, headers=headers).json()


def map_ids_to_sites(map_ids=None):
    map_ids = map_ids or [m["id"] for m in get_maps()]
    sites_by_id = {}
    for map_id in map_ids:
        sites = get_sites(map_id)
        sites_by_id[map_id] = sites["d"]
    return sites_by_id


@lru_cache
def get_site_description(site_id):
    url = GET_DESCRIPTION_URL_FORMAT.format(site_id)
    return requests.get(url, headers=headers).json()["d"]


def extract_table_entry_from_soup(soup, entry_name):

    td_tag = soup.find("td", text=lambda text: text and entry_name in text)

    if not td_tag:
        return None

    next_tag = td_tag.next_sibling
    while next_tag != None and len(next_tag.text.strip()) == 0:
        next_tag = next_tag.next_sibling

    return next_tag.text


def get_site_info(site_description):
    site_id = site_description["id"]
    lat = site_description["location"]["X"]
    long = site_description["location"]["Y"]
    relevant_map = find_map_by_coordinates(lat, long)
    if not relevant_map:
        print(
            "Warning: for some reason coordinates of site id {} are outside of any map.".format(
                site_id
            )
        )
        relevant_map_id = "?"
    else:
        relevant_map_id = relevant_map["id"]
    soup = BeautifulSoup(site_description["content"], "html.parser")
    image_tags = soup.find_all("image")
    photos, sketches = partition(
        is_sketch,
        [
            OPEN_IMAGE_URL_FORMAT.format(image_path=img["src"])
            for img in image_tags
            if "src" in img.attrs
        ],
    )
    periods = (
        (extract_table_entry_from_soup(soup, "תקופה") or "").strip().split(",")
    )
    remains = (
        (extract_table_entry_from_soup(soup, "שרידים") or "").strip().split(",")
    )
    return SiteInfo(
        name=site_description["name"],
        site_id=site_id,
        link=OPEN_IN_MAP_URL_FORMAT.format(
            map_id=relevant_map_id, site_id=site_id
        ),
        lat=lat,
        long=long,
        photos=photos,
        sketches=sketches,
        periods=periods,
        remains=remains,
    )


def bing_map_from_infos(infos):
    markers = "~".join(
        [
            BING_MARKER_FORMAT.format(
                x=info.long,
                y=info.lat,
                title=quote_plus_underscore(info.name),
                notes=quote_plus_underscore(info.link),
                link_url=quote_plus_underscore(info.link),
                photo=""
            )
            for info in infos
        ]
    )
    return BING_URL_FORMAT.format(markers=markers)


if __name__ == "__main__":
    # This generates the string that I put in static_maps
    import pickle

    print(pickle.dumps(get_maps()))
