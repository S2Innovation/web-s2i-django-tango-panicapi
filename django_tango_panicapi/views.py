# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import django_filters.rest_framework
from rest_framework import viewsets
from models import AlarmModel
from serializers import AlarmSerializer

# Create your views here.

def index(request):
    pass

class AlarmViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AlarmModel.objects.updated()
    serializer_class = AlarmSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ('tag', 'description', 'receivers', 'is_active', 'is_disabled')