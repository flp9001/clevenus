from django.shortcuts import render, get_object_or_404

from .models import UserProfile
from charts.utils import ChartCalc
# Create your views here.

def user_profile_view(request, username):
    user = get_object_or_404(UserProfile, user__username=username)

    chart = user.chart
    chart.save()
    chart = ChartCalc(chart.datetime, chart.time, chart.lat, chart.lng)

    planets = chart.planets[:10]
    #aspects = [a for a in chart.aspects if a.diff<10 and a.p1.i<10 and a.p2.i<10]
    aspects = [a for a in chart.aspects if a.p1.i<10 and a.p2.i<10 and a.diff<a.aspect.orb]
    params = dict()

    asc = chart.asc
    #asc = 0
    params['asc'] = asc
    for p in planets:
        params.update(p.get_svg_params())


    params['user'] = user
    params['chart'] = chart
    params['houses'] = chart.houses
    params['planets'] = planets
    params['aspects'] = aspects
    params['action'] = '/chart/post'

    return render(request, 'charts/detail.html', params)



def user_profile_view_old(request, username):
    user = get_object_or_404(UserProfile, user__username=username)
    chart = user.chart

    planets = chart.planetposition_set.all().select_related('planet',  'sign', 'house')[:10]
    aspects = chart.chartaspect_set.filter(diff__lt=10, p1__planet__index__lt=10, p2__planet__index__lt=10).select_related('p1__planet', 'p2__planet', 'aspect')
    params = dict()

    asc = chart.house_1
    #asc = 0
    params['asc'] = asc
    for p in planets:
        params.update(p.get_svg_params())



    params['chart'] = chart

    params['planets'] = planets
    params['aspects'] = aspects
    params['action'] = '/chart/post'

    return render(request, 'charts/detail.html', params)
