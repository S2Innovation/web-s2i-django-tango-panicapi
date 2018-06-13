# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-13 08:57
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_tango_panicapi', '0003_auto_20180612_2307'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlarmsApiSettingsModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_alarms_update', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0), verbose_name='Last alarms update')),
                ('last_history_update', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0), verbose_name='Last history update')),
                ('update_period', models.DurationField(default=datetime.timedelta(0, 5), verbose_name='Database update period')),
            ],
        ),
        migrations.DeleteModel(
            name='AlarmsSettings',
        ),
    ]