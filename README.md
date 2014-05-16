directions.py
=============

Provide a common Python API to major routing providers.
Please consult the terms of service of each provider before using them.
- Google - https://developers.google.com/maps/terms
- Mapquest - Contact for licensed data agreement
- Mapquest Open - http://developer.mapquest.com/web/info/terms-of-use
- Mapbox - (Directions API still in preview and subject to change) https://www.mapbox.com/tos/

Usage
-----
Create one of the available routers and call the `route()` method.
```
>>> import directions
>>> mq = directions.Mapquest(key)  # You must request a developer key from Mapquest
>>> routes = mq.route('1 magazine st. cambridge, ma', 'south station boston, ma')
```

See the help for `route()` for full documentation:
```
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
```

Examples
--------
```
mq = directions.Mapquest(key)
routes = mq.route('1 magazine st. cambridge, ma',
                  'south station boston, ma')

routes = mq.route('1 magazine st. cambridge, ma',
                  'south station boston, ma',
                  waypoints=['700 commonwealth ave. boston, ma'])
```

Use the points in a `LineString` as the complete set of waypoints.
```
line = LineString(...)
routes = mq.route(line)
```

The different types of location inputs can be mixed.
```
routes = mq.route(line.coords[0], 'south station boston, ma',
                  waypoints=[(-71.103972, 42.349324)])
```

Other Tools
-----------
[geojsonio.py](http://github.com/jwass/geojsonio.py) can be used to quickly display the route on a map. Note that it is against Google's ToS to do this with any of their routes.
```
routes = mq.route(...)
geojsonio.display(routes)
```
