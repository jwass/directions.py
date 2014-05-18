import unittest

from shapely.geometry import LineString, Point

from directions.base import _parse_points

class DirectionsTest(unittest.TestCase):
    def setUp(self):
        self.p = [(1,2), (3,4), (5,6), (7,8)]
        self.line = LineString(self.p)

    def test_origin_dest(self):
        result = _parse_points(self.p[0], self.p[-1])
        self.assertEqual([self.p[0], self.p[-1]], result)

    def test_origin_dest_waypoints(self):
        result = _parse_points(self.p[0], self.p[-1], self.p[1:-1])
        self.assertEqual(self.p, result)

    def test_line(self):
        result = _parse_points(self.line)
        self.assertEqual(self.p, result)

    def test_points(self):
        p0 = Point(self.line.coords[0])
        p1 = Point(self.line.coords[-1])
        result = _parse_points(p0, p1)
        self.assertEqual([self.p[0], self.p[-1]], result)

    def test_points_array(self):
        p0 = Point(self.p[0])
        p1 = Point(self.p[-1])
        result = _parse_points([p0, p1])
        self.assertEqual([self.p[0], self.p[-1]], result)

    def test_mixed_types(self):
        origin = 'blah'
        destination = Point(self.p[-1])
        points = self.p[1:-1]
        expected = list(self.p)  # Copy it
        expected[0] = 'blah'
        result = _parse_points(origin, destination, points)
        self.assertEqual(expected, result)

    def test_no_dest_waypoints(self):
        # Can't specify waypoints without destination
        with self.assertRaises(ValueError):
            _parse_points('origin', waypoints=['p1'])

    def test_bad_input(self):
        # Test points not length 2
        with self.assertRaises(ValueError):
            _parse_points(self.p[0], (1.0, 2.0, 3.0))
