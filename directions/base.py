import time

class Waypoint:
    VIA = 1
    STOP = 2

class Router:
    def __init__(self, name=None, rate_limit_dt=0):
        # Just a simple identifier
        if name is None:
            self.name = self.default_name

        # The min time delta in seconds between queries
        self._rate_limit_dt = rate_limit_dt

        # The time of the last query, None if it hasn't been hit yet
        self._last_query = None

    def raw_query(self, waypoints, **kwargs):
        return NotImplementedError()

    def rate_limit_wait(self):
        """
        Sleep if rate limiting is required based on current time and last
        query.

        """
        if self._rate_limit_dt and self._last_query is not None:
            dt = time.time() - self._last_query
            wait = self._rate_limit_dt - dt
            if wait > 0:
                time.sleep(wait)
        

    def format_output(self, data):
        return NotImplementedError()

    def route(self, arg, destination=None, waypoints=None, raw=False, **kwargs):
        """
        Query a route.

        route(locations): points can be
            - a sequence of locations
            - a Shapely LineString
        route(origin, destination, waypoints=None)
             - origin and destination are a single destination
             - waypoints are the points to be inserted between the
               origin and destination
             
             If waypoints is specified, destination must also be specified

        Each location can be:
            - string (will be geocoded by the routing provider. Not all
              providers accept this as input)
            - (longitude, latitude) sequence (tuple, list, numpy array, etc.)
            - Shapely Point with x as longitude, y as latitude

        Additional parameters
        ---------------------
        raw : bool, default False
            Return the raw json dict response from the service

        Returns
        -------
        list of Route objects
        If raw is True, returns the json dict instead of converting to Route
        objects

        Examples
        --------
        mq = directions.Mapquest(key)
        routes = mq.route('1 magazine st. cambridge, ma', 
                          'south station boston, ma')

        routes = mq.route('1 magazine st. cambridge, ma', 
                          'south station boston, ma', 
                          waypoints=['700 commonwealth ave. boston, ma'])

        # Uses each point in the line as a waypoint. There is a limit to the
        # number of waypoints for each service. Consult the docs.
        line = LineString(...)
        routes = mq.route(line)  

        # Feel free to mix different location types
        routes = mq.route(line.coords[0], 'south station boston, ma',
                          waypoints=[(-71.103972, 42.349324)])

        """
        points = _parse_points(arg, destination, waypoints)
        if len(points) < 2:
            raise ValueError('You must specify at least 2 points')

        self.rate_limit_wait()
        data = self.raw_query(points, **kwargs)
        self._last_query = time.time()

        if raw:
            return data
        return self.format_output(data)


def _parse_points(arg, destination=None, waypoints=None):
    # If destination is None, then arg is all the waypoints
    if destination is None:
        # waypoints must be None
        if waypoints is not None:
            raise ValueError('Cannot specify waypoints without destination')
        p = arg
    else:  # arg is origin
        if waypoints is None:
            p = [arg, destination]
        else:
            p = [arg] + waypoints + [destination]

    points = _waypoints(p)
    return points


def _waypoints(waypoints):
    if hasattr(waypoints, 'coords'):
        waypoints = waypoints.coords

    points = []
    for wp in waypoints:
        if isinstance(wp, str):
            p = wp
        elif hasattr(wp, 'coords'):
            coords = wp.coords
            if len(coords) != 1:
                raise ValueError('Non-point like object used in waypoints')
            p = coords[0]
        elif len(wp) == 2:
            p = wp
        else:
            raise ValueError('Non 2-tuple used in waypoints')

        points.append(p)

    return points


class Route:
    def __init__(self, coords, distance, duration, maneuvers=None, **kwargs):
        """
        Simple class to represent a single returned route

        Parameters
        ----------
        coords : sequence of (lon, lat) coordinates
        distance : length in meters of the route
        duration : estimated duration of the route in seconds
        kwargs : additional properties when converting to geojson

        """
        self.coords = coords
        self.distance = distance
        self.duration = duration
        self.properties = kwargs.copy()

        if maneuvers is None:
            maneuvers = []
        self.maneuvers = maneuvers

    @property
    def __geo_interface__(self):
        geom = {'type': 'LineString',
                'coordinates': self.coords}
        properties = self.properties.copy()
        properties.update({'distance': self.distance,
                           'duration': self.duration})

        f = {'type': 'Feature',
             'geometry': geom,
             'properties': properties}

        return f

    def geojson(self, include_maneuvers=True):
        if include_maneuvers:
            features = [self] + self.maneuvers
        else:
            features = [self]

        properties = self.properties.copy()
        properties.update({'distance': self.distance,
                           'duration': self.duration})

        return {'type': 'FeatureCollection',
                'properties': properties,
                'features': [f.__geo_interface__ for f in features]}

    @classmethod
    def from_geojson(cls, data):
        """
        Return a Route from a GeoJSON dictionary, as returned by Route.geojson()

        """
        properties = data['properties']
        distance = properties.pop('distance')
        duration = properties.pop('duration')

        maneuvers = []
        for feature in data['features']:
            geom = feature['geometry']
            if geom['type'] == 'LineString':
                coords = geom['coordinates']
            else:
                maneuvers.append(Maneuver.from_geojson(feature))

        return Route(coords, distance, duration, maneuvers, **properties)


class Maneuver:
    def __init__(self, coords, **kwargs):
        """
        Simple class to represent a maneuver.

        Todo: Add some remaining fields like maneuver text, type, etc.

        """
        self.coords = coords
        self.properties = kwargs.copy()

    @property
    def __geo_interface__(self):
        geom = {'type': 'Point',
                'coordinates': self.coords}

        f = {'type': 'Feature',
             'geometry': geom,
             'properties': self.properties}

        return f

    @classmethod
    def from_geojson(cls, data):
        """
        Return a Maneuver from a GeoJSON dictionary

        """
        coords = data['geometry']['coordinates']
        return Maneuver(coords, **data['properties'])
