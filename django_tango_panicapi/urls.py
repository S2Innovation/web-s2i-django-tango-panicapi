from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views


# create routers
panicapi_router = DefaultRouter()
panicapi_router.register(r'alarms', views.AlarmViewset)
panicapi_router.register(r'history', views.AlarmHistoryViewset)


urlpatterns = [
    url(r'^sync', views.synch_db),
    url(r'^', include(panicapi_router.urls)),
]