# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import django_filters.rest_framework
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from models import AlarmModel, AlarmHistoryModel
from serializers import AlarmSerializer, AlarmHistorySerializer

# Create your views here.


def index(request):
    pass


class AlarmsPaginator(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000000

class AlarmViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AlarmModel.objects.updated()
    serializer_class = AlarmSerializer
    pagination_class = AlarmsPaginator
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = {
        'tag': ['exact', 'icontains', 'contains', ],
        'description': ['exact', 'icontains', 'contains', ],
        'receivers': ['exact', 'icontains', 'contains', ],
        'is_active': ['exact'],
        'is_disabled': ['exact'],
        'severity': ['exact', 'icontains', 'contains', 'in', ],
        'state': ['exact', 'icontains', 'contains', 'in', ],
    }


class AlarmHistoryViewset(viewsets.ReadOnlyModelViewSet):

    queryset = AlarmHistoryModel.objects.updated().order_by('-date')

    serializer_class = AlarmHistorySerializer

    pagination_class = AlarmsPaginator


    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = {
        'date': ['exact', 'range','date__gt', 'date__lt', ],
        'comment': ['exact', 'icontains', 'contains', ],
        'alarm__tag': ['exact', 'icontains', 'contains', 'startswith']
    }