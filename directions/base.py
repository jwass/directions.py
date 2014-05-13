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

    def route(self, origin, destination, waypoints=None, **kwargs):
        return NotImplementedError()
