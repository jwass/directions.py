"""
Classes for major routing providers
* Google
* Mapquest
* Mapquest Open
* Mapbox

Please consult the terms of service of each provider before using the service
Google - https://developers.google.com/maps/terms
Mapquest - Contact for licensed data agreement
Mapquest Open - http://developer.mapquest.com/web/info/terms-of-use
Mapbox - https://www.mapbox.com/tos/

"""
import json

import polycomp
import requests

from base import Router


class Google(Router):
    url = 'http://maps.googleapis.com/maps/api/directions/json'

    # https://developers.google.com/maps/documentation/directions/
    def _convert_coordinate(self, p):
        if isinstance(p, basestring):
            return p
        # Google wants lat / lon
        return '{0[1]},{0[0]}'.format(p)

    def raw_query(self, waypoints, **kwargs):
        origin = waypoints[0]
        destination = waypoints[-1]
        vias = waypoints[1:-1]
        # This assumes you're not running Python on a device with a location
        # sensor.
        payload = {'origin': self._convert_coordinate(origin),
                   'destination': self._convert_coordinate(destination),
                   'sensor': 'false'}
        if vias:
            payload['waypoints'] = '|'.join(self._convert_coordinate(wp)
                                            for wp in waypoints)
        payload.update(kwargs)

        r = requests.get(self.url, params=payload)
        r.raise_for_status()

        return r.json()

    def format_output(self, data):
        features = []
        for r in data['routes']:
            # For now, just use the 'overview_polyline'.
            # TODO: Use the higher res leg polylines
            latlons = polycomp.decompress(r['overview_polyline']['points'])
            # Reverse lat/lon to be lon/lat for GeoJSON
            coords = [tuple(reversed(c)) for c in latlons]
            duration = sum(leg['duration']['value'] for leg in r['legs'])
            distance = sum(leg['distance']['value'] for leg in r['legs'])
            f = self.route_to_feature(coords, distance, duration)
            features.append(f)

        return self.feature_collection(features)


class Mapquest(Router):
    # http://www.mapquestapi.com/directions/ 
    url = 'http://www.mapquestapi.com/directions/v2/route'

    def __init__(self, key):
        self.key = key

    def _convert_location(self, location, t='s'):
        if isinstance(location, basestring):
            return {'street': location, 'type': t}
        else:
            return {'latLng': {'lat': location[1], 'lng': location[0]},
                    'type': t}

    def raw_query(self, waypoints, **kwargs):
        params = {
            'key': self.key,
            'inFormat': 'json',
            'outFormat': 'json',
        }

        # Mapquest takes in locations as an array
        locations = [self._convert_location(waypoints[0])]
        if waypoints:
            locations.extend(self._convert_location(loc, 'v')
                             for loc in waypoints[1:-1])
        locations.append(self._convert_location(waypoints[-1]))

        data = {
            'locations': locations,
            'options': {
                'avoidTimedConditions': False,
                'shapeFormat': 'cmp',
                'generalize': 0,  # No simplification
                'unit': 'k',
            },
        }
        data = json.dumps(data, separators=(',', ':'))

        r = requests.post(self.url,
                          params=params,
                          data=data)
        r.raise_for_status()
        data = r.json()
        status_code = data['info']['statuscode']
        if status_code != 0:
            raise Exception(data['info']['messages'][0])

        return data

    def format_output(self, data):
        latlons = polycomp.decompress(data['route']['shape']['shapePoints'])
        coords = [tuple(reversed(c)) for c in latlons]
        duration = data['route']['time']
        distance = data['route']['distance'] * 1000  # km to m
        feature = self.route_to_feature(coords, distance, duration)

        return self.feature_collection([feature])


class MapquestOpen(Mapquest):
    # http://open.mapquestapi.com/directions/
    # This is the same interface as Mapquest (for now) but just hits
    # a different url
    url = 'http://open.mapquestapi.com/directions/v2/route'


class Mapbox(Router):
    # https://www.mapbox.com/developers/api/directions/
    def __init__(self, mapid):
        self.mapid = mapid

    def _convert_coordinate(self, p):
        return '{0[0]},{0[1]}'.format(p)

    def raw_query(self, waypoints, **kwargs):
        baseurl = 'http://api.tiles.mapbox.com/v3/{mapid}/directions/driving/{waypoints}.json'
        formatted_points = ';'.join(self._convert_coordinate(p)
                                    for p in waypoints)

        url = baseurl.format(mapid=self.mapid, waypoints=formatted_points)
        payload = {'alternatives': 'false'}
        r = requests.get(url, params=payload)

        r.raise_for_status()
        return r.json()

    def format_output(self, data):
        features = [self.route_to_feature(r['geometry']['coordinates'],
                                          r['distance'],
                                          r['duration'])
                    for r in data['routes']]
        return self.feature_collection(features)
