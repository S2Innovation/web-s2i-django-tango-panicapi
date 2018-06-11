from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from . import views

# create router
panicapi_router = DefaultRouter()
panicapi_router.register(r'alarms', views.AlarmViewset)

urlpatterns = [
    url(r'^', include(panicapi_router.urls)),
]