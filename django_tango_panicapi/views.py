# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, HttpResponse
import django_filters.rest_framework
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from threading import Lock

from models import AlarmModel, AlarmHistoryModel
from serializers import AlarmSerializer, AlarmHistorySerializer

# Create your views here.

sync_lock = Lock()


def index(request):
    pass


def synch_db(request):
    """synchronize database with alarms"""
    global sync_lock
    if sync_lock.acquire(False):
        try:
            AlarmModel.objects.updated()
            AlarmHistoryModel.objects.updated()
        finally:
            sync_lock.release()
    return HttpResponse('ok', content_type='application/text')

class AlarmsPaginator(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000000

class AlarmViewset(viewsets.ReadOnlyModelViewSet):
    queryset = AlarmModel.objects.all()
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

    queryset = AlarmHistoryModel.objects.all().order_by('-date')

    serializer_class = AlarmHistorySerializer

    pagination_class = AlarmsPaginator


    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = {
        'date': ['exact', 'range','date__gt', 'date__lt', ],
        'comment': ['exact', 'icontains', 'contains', ],
        'alarm__tag': ['exact', 'icontains', 'contains', 'startswith']
    }