class Router:
    def raw_query(self, waypoints, **kwargs):
        return NotImplementedError()

    def format_output(self, data):
        return NotImplementedError()

    def route(self, arg, destination=None, waypoints=None, raw=False, **kwargs):
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
        if len(points) < 2:
            raise ValueError('You must specify at least 2 points')

        data = self.raw_query(points, **kwargs)
        if raw:
            return data
        return self.format_output(data)


def _waypoints(waypoints):
    if hasattr(waypoints, 'coords'):
        waypoints = waypoints.coords

    points = []
    for wp in waypoints:
        if isinstance(wp, basestring):
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
    def __init__(self, coords, distance, duration, **kwargs):
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
        self.props = kwargs.copy()

    @property
    def __geo_interface__(self):
        geom = {'type': 'LineString',
                'coordinates': self.coords}
        props = self.props.copy()
        props.update({'distance': self.distance,
                      'duration': self.duration})

        f = {'type': 'Feature',
             'geometry': geom,
             'properties': props}

        return f

    def geojson(self):
        return {'type': 'FeatureCollection',
                'features': [self.__geo_interface__]}
