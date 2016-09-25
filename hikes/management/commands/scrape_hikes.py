import json
import os
import re

import requests
from bs4 import BeautifulSoup, Comment
from django.conf import settings
from django.core.management.base import BaseCommand


MAPS_REGEX = re.compile(r'.*google\.com/maps')
TRIMBLE_REGEX = re.compile(r'trimbleoutdoors\.com')


class Command(BaseCommand):
    help = 'Scrape hikes from roanokeoutside.com. Re-run if content is updated on site.'

    def add_arguments(self, parser):
        parser.add_argument('--hikes_url', default='http://www.roanokeoutside.com/land/hiking/all-hikes/',
                            help='Link to Roanoke Outside Hikes page.')
        parser.add_argument('--no_write', action='store_true', help='Output to stdout rather than a file.')
        parser.add_argument('-f', '--file', default=os.path.join(settings.BASE_DIR, 'hikes/data/all_hikes.json'),
                            help='Path to output file.')

    def handle(self, *args, **options):
        hikes = []
        hikes_html = requests.get(options['hikes_url']).content
        hikes_soup = BeautifulSoup(hikes_html, 'html.parser')
        hike_items = hikes_soup.find('div', class_='primary').find_all('li', class_='detail-list__item')

        for hike_item in hike_items:
            name = ' '.join(hike_item.a.stripped_strings)
            content_tag = hike_item.find(class_='detail-list__content')
            description = list(filter(None, self._description_from_content(content_tag)))

            location = self._location_from_content(content_tag)
            if not location:
                continue

            map_embed = self._map_embed_from_content(content_tag)

            hikes.append({
                'name': name,
                'description': description,
                'location': location,
                'map_embed': map_embed,
            })

        if not options['no_write']:
            with open(options['file'], mode='w') as hikes_file:
                json.dump(hikes, hikes_file)
        return json.dumps(hikes)

    def _description_from_content(self, content):
        """Pull the discription as a list of strings from the detail list content body."""
        for tag in content.children:
            if isinstance(tag, str):
                if not isinstance(tag, Comment):
                    yield tag.strip()
                continue
            elif 'detail-list__actions-list' in tag.get('class', []):
                continue
            for string in tag.stripped_strings:
                yield string

    def _location_from_content(self, content):
        """Pull the lat/lon or address from Google maps URL in the detail list content body."""
        directions = content.find(href=MAPS_REGEX)
        if not directions:
            return None
        lat_match = re.match(r'.*/maps.*q=.??(-?\d+\.\d+)\+(-?\d+\.\d+).*', directions['href'])
        if lat_match:
            return lat_match.group(1, 2)
        loc_match = re.match(r'.*/maps/place/(.*)', directions['href'])
        if loc_match:
            return ' '.join(loc_match.group(1).split('+'))
        return None

    def _map_embed_from_content(self, content):
        """Create the trimble outdoors embed link from the trip ID in the detail list content body."""
        map = content.find(href=TRIMBLE_REGEX)
        if not map:
            return None
        trip_id = re.match(r'.*(?:/.*tripId=|ViewTrip/)(\d+).*', map['href']).group(1)
        return 'http://www.trimbleoutdoors.com/Maps/EmbeddedMap.aspx?tripId={}'.format(trip_id)
