import requests
from pprint import pprint

url = "https://survey.antiquities.org.il/aspxService/Service.aspx/GetMaps"

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


def find_map_by_coordinates(
    maps,
    lat,
    long,
    delta_lat=0.04510300056818182,  # From running some experiments on the data set using plt.hist and seeing the distribution
    delta_long=0.05287043108333312
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
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Request was successful.")
        maps_data = response.json()["d"]
    else:
        print(f"Failed to retrieve data: {response.status_code}")
    return maps_data


if __name__ == "__main__":
    import pickle
    print(pickle.dumps(get_maps()))