import json
import os

from django.conf import settings
from mapbox import Geocoder


def _get_lat_lon(location):
    geocoder = Geocoder(access_token=settings.MAPBOX_TOKEN)
    response = geocoder.forward(location)
    response.raise_for_status()
    longitude, latitude = response.geojson()['features'][0]['geometry']['coordinates']
    return (latitude, longitude)


def get_all_hikes():
    all_hikes_file = os.path.join(settings.BASE_DIR, 'hikes/data/all_hikes.json')
    with open(all_hikes_file) as hikes_file:
        proceessed_hikes = process_hikes(json.load(hikes_file))
    return proceessed_hikes


def process_hikes(hikes):
    for hike in hikes:
        if not isinstance(hike['location'], (tuple, list)):
            hike['location'] = _get_lat_lon(hike['location'])
    return hikes

