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

from base import Router, Route, Maneuver, Waypoint


class Google(Router):
    url = 'http://maps.googleapis.com/maps/api/directions/json'

    def __init__(self, *args, **kwargs):
        Router.__init__(self, *args, **kwargs)

    # https://developers.google.com/maps/documentation/directions/
    def _convert_coordinate(self, p, t=Waypoint.VIA):
        if isinstance(p, basestring):
            return p
        if t == Waypoint.VIA:
            via = 'via:'
        else:
            via = ''

        # Google wants lat / lon
        return '{via}{0[1]:.6f},{0[0]:.6f}'.format(p, via=via)

    def _query_params(self, waypoints):
        origin = waypoints[0]
        destination = waypoints[-1]
        vias = waypoints[1:-1]
        # This assumes you're not running Python on a device with a location
        # sensor.
        payload = {'origin': self._convert_coordinate(origin, t=None),
                   'destination': self._convert_coordinate(destination, t=None),
                   'sensor': 'false',
                   'units': 'metric'}
        if vias:
            payload['waypoints'] = '|'.join(self._convert_coordinate(v)
                                            for v in vias)
        return payload

    def raw_query(self, waypoints, **kwargs):
        payload = self._query_params(waypoints)
        payload.update(kwargs)

        r = requests.get(self.url, params=payload)
        r.raise_for_status()

        return r.json()

    def format_output(self, data):
        routes = []
        for r in data['routes']:
            # For now, just use the 'overview_polyline'.
            # TODO: Use the higher res leg polylines
            latlons = polycomp.decompress(r['overview_polyline']['points'])
            # Reverse lat/lon to be lon/lat for GeoJSON
            coords = [tuple(reversed(c)) for c in latlons]
            duration = sum(leg['duration']['value'] for leg in r['legs'])
            distance = sum(leg['distance']['value'] for leg in r['legs'])

            maneuvers = []
            # Legs are the spans of the route between waypoints desired. If
            # there are no waypoints, there will only be 1 leg
            for leg in r['legs']:
                for step in leg['steps']:
                    loc = step['start_location']
                    m = Maneuver((loc['lng'], loc['lat']),
                                 text=step['html_instructions'])
                    maneuvers.append(m)
            route = Route(coords, distance, duration, maneuvers=maneuvers)
            routes.append(route)

        return routes


class Mapquest(Router):
    # http://www.mapquestapi.com/directions/
    url = 'http://www.mapquestapi.com/directions/v2/route'

    def __init__(self, key, *args, **kwargs):
        Router.__init__(self, *args, **kwargs)
        self.key = key

    def _convert_location(self, location, t=Waypoint.VIA):
        if t == Waypoint.VIA:
            via = 'v'
        else:
            via = 's'
        if isinstance(location, basestring):
            return {'street': location, 'type': via}
        else:
            return {'latLng': {'lat': location[1], 'lng': location[0]},
                    'type': via}

    def _format_waypoints(self, waypoints):
        # Mapquest takes in locations as an array
        locations = [self._convert_location(waypoints[0], t=Waypoint.STOP)]
        if waypoints:
            locations.extend(self._convert_location(loc, t=Waypoint.VIA)
                             for loc in waypoints[1:-1])
        locations.append(self._convert_location(waypoints[-1], t=Waypoint.STOP))

        return locations

    def raw_query(self, waypoints, **kwargs):
        params = {
            'key': self.key,
            'inFormat': 'json',
            'outFormat': 'json',
        }

        locations = self._format_waypoints(waypoints)
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

        maneuvers = []
        for leg in data['route']['legs']:
            for m_in in leg['maneuvers']:
                loc = m_in['startPoint']
                m = Maneuver((loc['lng'], loc['lat']),
                             text=m_in['narrative'])
                maneuvers.append(m)
        r = Route(coords, distance, duration, maneuvers=maneuvers)

        return [r]


class MapquestOpen(Mapquest):
    # http://open.mapquestapi.com/directions/
    # This is the same interface as Mapquest (for now) but just hits
    # a different url
    url = 'http://open.mapquestapi.com/directions/v2/route'


class Mapbox(Router):
    # https://www.mapbox.com/developers/api/directions/
    def __init__(self, mapid, *args, **kwargs):
        Router.__init__(self, *args, **kwargs)
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
        routes = []
        for r in data['routes']:
            maneuvers = [Maneuver(s['maneuver']['location']['coordinates'],
                                  text=s['maneuver']['instruction'])
                         for s in r['steps']]
            route = Route(r['geometry']['coordinates'],
                          r['distance'],
                          r['duration'], maneuvers=maneuvers)
            routes.append(route)
        return routes
