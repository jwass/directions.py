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

    def raw_query(self, origin, destination, waypoints=None, **kwargs):
        return NotImplementedError()

    def format_output(self, data):
        return NotImplementedError()

    def route(self, origin, destination, waypoints=None, **kwargs):
        data = self.raw_query(origin, destination, waypoints, **kwargs)
        return self.format_output(data)

