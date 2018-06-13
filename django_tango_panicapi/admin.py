# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from models import AlarmsApiSettingsModel, AlarmModel, AlarmHistoryModel

# Register your models here.
@admin.register(AlarmsApiSettingsModel, AlarmModel, AlarmHistoryModel)
class AlarmsApiAdminPanel(admin.ModelAdmin):
    pass