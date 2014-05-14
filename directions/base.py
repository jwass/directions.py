class Router:
    def route_to_feature(self, coords, distance, duration, **kwargs):
        """
        Turn a route into a GeoJSON feature.

        """
        geom = {'type': 'LineString',
                'coordinates': coords}
        props = kwargs.copy()
        props.update({'distance' : distance,
                      'duration' : duration})

        f = {'type': 'Feature',
             'geometry': geom,
             'properties': props}

        return f

    def feature_collection(self, features):
        return {'type' : 'FeatureCollection',
                'features' : features}

    def raw_query(self, waypoints, **kwargs):
        return NotImplementedError()

    def format_output(self, data):
        return NotImplementedError()

    def route(self, arg, destination=None, waypoints=None, **kwargs):
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
