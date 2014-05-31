import unittest

from directions import Mapquest, MapquestOpen, Google

class RoutersTest(unittest.TestCase):
    def setUp(self):
        self.google = Google(rate_limit_dt=1.0)

    def test_google_via(self):
        points = [(45.0, 55.0), (50.0, 70.0), (65.0, 75.0)]
        payload = self.google._query_params(points)

        waypoints = payload['waypoints'].split('|')
        self.assertEquals(1, len(waypoints))
        self.assert_('via' not in payload['origin'])
        self.assert_('via' not in payload['destination'])
        for wp in waypoints:
            self.assert_('via' in wp)
