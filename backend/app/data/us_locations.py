"""US states and cities with coordinates for weather."""

# state -> list of (city_name, lat, lon)
US_STATES_CITIES = {
    "Alabama": [("Montgomery", 32.3668, -86.3000), ("Birmingham", 33.5207, -86.8025)],
    "Alaska": [("Anchorage", 61.2181, -149.9003), ("Juneau", 58.3019, -134.4197)],
    "Arizona": [("Phoenix", 33.4484, -112.0740), ("Tucson", 32.2226, -110.9747)],
    "Arkansas": [("Little Rock", 34.7465, -92.2896), ("Fayetteville", 36.0626, -94.1574)],
    "California": [("Los Angeles", 34.0522, -118.2437), ("San Francisco", 37.7749, -122.4194), ("San Diego", 32.7157, -117.1611), ("Sacramento", 38.5816, -121.4944)],
    "Colorado": [("Denver", 39.7392, -104.9903), ("Boulder", 40.0150, -105.2705)],
    "Connecticut": [("Hartford", 41.7658, -72.6734), ("New Haven", 41.3083, -72.9279)],
    "Delaware": [("Wilmington", 39.7391, -75.5398), ("Dover", 38.9108, -75.5277)],
    "Florida": [("Miami", 25.7617, -80.1918), ("Orlando", 28.5383, -81.3792), ("Tampa", 27.9506, -82.4572)],
    "Georgia": [("Atlanta", 33.7490, -84.3880), ("Savannah", 32.0809, -81.0912)],
    "Hawaii": [("Honolulu", 21.3099, -157.8581), ("Hilo", 19.7297, -155.0900)],
    "Idaho": [("Boise", 43.6150, -116.2023), ("Idaho Falls", 43.4917, -112.0340)],
    "Illinois": [("Chicago", 41.8781, -87.6298), ("Springfield", 39.7817, -89.6501)],
    "Indiana": [("Indianapolis", 39.7684, -86.1581), ("Fort Wayne", 41.0793, -85.1394)],
    "Iowa": [("Des Moines", 41.5868, -93.6250), ("Iowa City", 41.6611, -91.5302)],
    "Kansas": [("Wichita", 37.6872, -97.3301), ("Kansas City", 39.1142, -94.6275)],
    "Kentucky": [("Louisville", 38.2527, -85.7585), ("Lexington", 38.0406, -84.5037)],
    "Louisiana": [("New Orleans", 29.9511, -90.0715), ("Baton Rouge", 30.4515, -91.1871)],
    "Maine": [("Portland", 43.6591, -70.2568), ("Augusta", 44.3106, -69.7795)],
    "Maryland": [("Baltimore", 39.2904, -76.6122), ("Annapolis", 38.9784, -76.4922)],
    "Massachusetts": [("Boston", 42.3601, -71.0589), ("Cambridge", 42.3736, -71.1097)],
    "Michigan": [("Detroit", 42.3314, -83.0458), ("Ann Arbor", 42.2808, -83.7430)],
    "Minnesota": [("Minneapolis", 44.9778, -93.2650), ("Saint Paul", 44.9537, -93.0900)],
    "Mississippi": [("Jackson", 32.2988, -90.1848), ("Gulfport", 30.3674, -89.0928)],
    "Missouri": [("Kansas City", 39.0997, -94.5786), ("Saint Louis", 38.6270, -90.1994)],
    "Montana": [("Billings", 45.7833, -108.5007), ("Missoula", 46.8721, -113.9940)],
    "Nebraska": [("Omaha", 41.2565, -95.9345), ("Lincoln", 40.8258, -96.6852)],
    "Nevada": [("Las Vegas", 36.1699, -115.1398), ("Reno", 39.5296, -119.8138)],
    "New Hampshire": [("Manchester", 42.9956, -71.4548), ("Concord", 43.2081, -71.5376)],
    "New Jersey": [("Newark", 40.7357, -74.1724), ("Jersey City", 40.7178, -74.0431)],
    "New Mexico": [("Albuquerque", 35.0844, -106.6504), ("Santa Fe", 35.6870, -105.9378)],
    "New York": [("New York City", 40.7128, -74.0060), ("Buffalo", 42.8864, -78.8784), ("Rochester", 43.1566, -77.6088)],
    "North Carolina": [("Charlotte", 35.2271, -80.8431), ("Raleigh", 35.7796, -78.6382)],
    "North Dakota": [("Fargo", 46.8772, -96.7898), ("Bismarck", 46.8083, -100.7837)],
    "Ohio": [("Columbus", 39.9612, -82.9988), ("Cleveland", 41.4993, -81.6944)],
    "Oklahoma": [("Oklahoma City", 35.4676, -97.5164), ("Tulsa", 36.1539, -95.9928)],
    "Oregon": [("Portland", 45.5152, -122.6784), ("Eugene", 44.0521, -123.0868)],
    "Pennsylvania": [("Philadelphia", 39.9526, -75.1652), ("Pittsburgh", 40.4406, -79.9959)],
    "Rhode Island": [("Providence", 41.8240, -71.4128), ("Newport", 41.4901, -71.3128)],
    "South Carolina": [("Charleston", 32.7765, -79.9311), ("Columbia", 34.0522, -81.0320)],
    "South Dakota": [("Sioux Falls", 43.5446, -96.7311), ("Rapid City", 44.0805, -103.2310)],
    "Tennessee": [("Nashville", 36.1627, -86.7816), ("Memphis", 35.1495, -90.0490)],
    "Texas": [("Houston", 29.7604, -95.3698), ("Dallas", 32.7767, -96.7970), ("Austin", 30.2672, -97.7431), ("San Antonio", 29.4241, -98.4936)],
    "Utah": [("Salt Lake City", 40.7608, -111.8910), ("Provo", 40.2338, -111.6585)],
    "Vermont": [("Burlington", 44.4759, -73.2121), ("Montpelier", 44.2601, -72.5754)],
    "Virginia": [("Virginia Beach", 36.8529, -75.9780), ("Richmond", 37.5407, -77.4360)],
    "Washington": [("Seattle", 47.6062, -122.3321), ("Spokane", 47.6588, -117.4260)],
    "West Virginia": [("Charleston", 38.3498, -81.6326), ("Morgantown", 39.6295, -79.9559)],
    "Wisconsin": [("Milwaukee", 43.0389, -87.9065), ("Madison", 43.0731, -89.4012)],
    "Wyoming": [("Cheyenne", 41.1399, -104.8202), ("Jackson", 43.4799, -110.7624)],
    "District of Columbia": [("Washington", 38.9072, -77.0369)],
}


def get_coords(state: str, city: str) -> tuple[float, float] | None:
    """Return (lat, lon) for state+city, or None."""
    cities = US_STATES_CITIES.get(state)
    if not cities:
        return None
    for name, lat, lon in cities:
        if name == city:
            return (lat, lon)
    return None
