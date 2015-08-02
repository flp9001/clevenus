from math import pi, sin, cos
import pytz
from  datetime import datetime,  time
import swisseph as swe

swe.set_ephe_path('/usr/share/libswe/ephe/')

from .models import Planet, Aspect, Sign

PLANETS = {p.index: p for p in Planet.objects.all().order_by('index')}
ASPECTS = {(a.p1.index, a.p2.index, a.degrees): a for a in Aspect.objects.all().select_related('p1', 'p2')}
SIGNS = {s.index: s for s in Sign.objects.all().order_by('index')}


class PlanetPosition(object):
    def __init__(self, i, eph, asc=0, house_cusps=None):
        x, y, z, dx, dy, dz = eph
        self.i = i
        self.planet = PLANETS[i]
        self.code = PLANETS[i].code

        self.x = x
        self.angle = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz

        self.asc = asc
        self.sign_i = int(x / 30)
        self.sign = SIGNS[self.sign_i]
        self.house_i = -1
        if house_cusps:
            self.house_i = self.calc_house(self.x, house_cusps)

    def calc_house(self, angle, house_cusps):
        for i in range(12):
            if house_cusps[i] > house_cusps[(i+1) % 12]:
                if house_cusps[i] < angle or angle <= house_cusps[(i+1) % 12]:
                    return i
            else:
                if house_cusps[i] < angle <= house_cusps[(i+1) % 12]:
                    return i

    def get_x(self, planet_radius=220, chart_center_x=300):
        x = cos((self.x + 180 - self.asc) * pi / 180.0) * planet_radius + chart_center_x
        return x

    def get_y(self, planet_radius=220, chart_center_y=300):
        y = -sin((self.x + 180 - self.asc) * pi / 180.0) * planet_radius + chart_center_y
        return y

    def get_x_aspect(self):
        return self.get_x(planet_radius=200)

    def get_y_aspect(self):
        return self.get_y(planet_radius=200)

    def get_svg_params(self, planet_radius=220, planet_size=7, planet_circle=10):
        params = dict()
        planet_scale = planet_size * 2 / 100.0
        chart_center_x = 300
        chart_center_y = 300
        p_x = self.get_x(planet_radius, chart_center_x)
        p_y = self.get_y(planet_radius, chart_center_y)

        visibility = True
        params[self.code + '_visibility'] = 'visible' if visibility else 'hidden'
        params[self.code + '_x'] = p_x
        params[self.code + '_y'] = p_y
        params[self.code + '_circle'] = planet_circle
        params[self.code + '_scale'] = planet_scale

        params[self.code + '_x_corner'] = p_x - planet_size
        params[self.code + '_y_corner'] = p_y - planet_size
        return params

class ChartAspect(object):

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.diff, self.exact, self.aspect = self.calc(p1, p2)

    def calc(self, p1, p2):
        a1 = p1.x
        a2 = p2.x
        angle = min(abs(a1 - a2), abs(360 - abs(a1 - a2)))
        a, b = divmod(angle, 30)
        c, d = map(abs, divmod(angle, -30))
        diff, exact = min((b, a), (d, c))
        exact *= 30
        exact = int(exact)
        #if exact == 30 or exact == 150:
        #    return None

        if (p1.i, p2.i, exact) in ASPECTS:
            aspect = ASPECTS[(p1.i, p2.i, exact)]
        else:
            aspect = None

        return diff, exact, aspect

    def get_svg(self):
        params = dict()
        params['id'] = '%s_%s_aspect' % (self.p1.planet.code, self.p2.planet.code)
        params['x1'] = self.p1.get_x_aspect()
        params['y1'] = self.p1.get_y_aspect()
        params['x2'] = self.p2.get_x_aspect()
        params['y2'] = self.p2.get_y_aspect()

        color = 'black'
        if self.exact == 60 or self.exact == 120:
            color = 'blue'
        if self.exact == 90 or self.exact == 180:
            color = 'red'

        params['color'] = color

        svg = '<svg class="svg_aspect"><line id="{id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:{color};stroke-width:1"></line></svg>'.format(
            **params)
        return svg


class ChartCalc(object):
    def __init__(self, datetime, lat=None, lng=None):
        self.datetime = datetime
        self.lat = lat
        self.lng = lng
        self.asc = 0
        self.planets = self.calc(self.lat, self.lng)
        self.aspects = self.calc_aspects(self.planets)

    def calc(self, lat, lng, n_planets=10):
        if self.datetime.tzinfo is None:
            self.datetime = pytz.utc.localize(self.datetime)
        datetime_utc = self.datetime.astimezone(pytz.utc)
        j = self.julday(datetime_utc)
        ephs = [swe.calc_ut(j, i) for i in range(n_planets)]
        asc = 0
        houses = None
        if lat and lng:
            houses = swe.houses(j, self.lat, self.lng)[0]
            asc = houses[0]
            self.asc = asc

        positions = []
        for i, eph in enumerate(ephs):
            positions.append(PlanetPosition(i, eph, asc, houses))

        return positions

    def calc_aspects(self, positions):
        aspects = []
        for p1 in positions:
            for p2 in positions:
                if p1 != p2:
                    aspects.append(ChartAspect(p1, p2))
        return filter(lambda x: x.aspect is not None, aspects)

    def julday(self, d):
        j = swe.julday(d.year, d.month, d.day, d.hour + d.minute / 60.0)
        return j

    def update_datetime_city(self):
        if self.time:
            self.datetime = datetime.combine(self.date, self.time)
        else:
            self.datetime = datetime.combine(self.date, time(12, 0))

        if self.city:
            self.datetime = self.city.timezone.localize(self.datetime)
            self.city_name = self.city.name
            self.lat = self.city.lat
            self.lng = self.city.lng
        else:
            self.datetime = pytz.utc.localize(self.datetime)

