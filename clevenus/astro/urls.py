from django.conf.urls import patterns, include, url
from .views import *

urlpatterns = patterns('',
    url(r'planet-in-sign/(?P<planet>\w+)/(?P<sign>\w+)/', planet_in_sign, name='planet-in-sign'),
    url(r'planet-in-house/(?P<planet>\w+)/(?P<house>\w+)/', planet_in_house, name='planet-in-house'),
    url(r'aspect/(?P<planet1>\w+)/(?P<aspect_type>\w+)/(?P<planet2>\w+)/', aspect, name='aspect'),
)