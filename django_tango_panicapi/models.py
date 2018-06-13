# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import OperationalError
from panic import alarmapi
from PyTangoArchiving import snap
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create your models here.
ALARM_PRIORITIES = [
    ('ALARM', 'ALARM'), ('WARNING','WARNING'), ('INFO','INFO'), ('ERROR','ERROR'), ('DEBUG','DEBUG'),
]

ALARM_STATES = [
    ('NORM', 'Not active'),
    ('UNACK', 'Active, not acknowledged'),
    ('RTNUN', 'Activated but condition return to normal'),
    ('ACKED', 'Active, acknowledged'),
    ('OOSRV', 'Active, not acknowledged'),
    ('ERROR', 'Error'),
    ('UNACK', 'Active, not acknowledged'),
    ('DSUPR', 'DSUPR'),
    ('SHLVD', 'SHLVD'),

]

Alarm = alarmapi.Alarm
alarms = alarmapi.api()


class AlarmsSettings(models.Model):
    last_alarms_update = models.DateTimeField(auto_now=True)
    last_history_update = models.DateTimeField(auto_now=True)
    update_period = models.DurationField()


class AlarmQueryset(models.QuerySet):
    """Queryset to manage alarm database."""

    def updated(self):
        """Returns a queryset after database synchronization"""

        # iterate through defined alarms and do update
        try:
            for alarm_tag in alarms.keys():
                # find object in a database
                alarm, is_created = AlarmModel.objects.get_or_create(tag=alarm_tag)
                assert isinstance(alarm, AlarmModel)

                # set fields
                panic_alarm = alarms[alarm_tag]
                assert isinstance(panic_alarm, Alarm)
                alarm.tag = alarm_tag
                alarm.severity = panic_alarm.get_priority()
                alarm.state = panic_alarm.get_state()
                alarm.description = panic_alarm.description
                alarm.formula = panic_alarm.get_condition()
                alarm.receivers = panic_alarm.get_annunciators()
                alarm.wiki_link = panic_alarm.get_wiki_link()
                alarm.is_disabled = panic_alarm.disabled
                alarm.is_active = panic_alarm.is_active()
                if panic_alarm.time != 0:
                    alarm.activation_time = datetime.fromtimestamp(panic_alarm.time)
                else:
                    alarm.activation_time = None

                # save to database
                alarm.save()
        except OperationalError as oe:
            logger.warning('There is an operational error: %s \n'
                           'If it is before any migration it is normal for .updated() method '
                           'tries to use a table which is not yet created.' % str(oe))

        return self


class AlarmModel(models.Model):

    # set custom manager based on custom queryset
    objects = AlarmQueryset.as_manager()

    # fields
    tag = models.CharField(max_length=128, primary_key=True, verbose_name='Name/Tag')
    severity = models.CharField(max_length=128,
                                choices=ALARM_PRIORITIES,
                                blank=True, verbose_name='Severity')
    state = models.CharField(max_length=128, choices=ALARM_STATES, blank=True, verbose_name='State')
    description = models.TextField(blank=True, verbose_name='Description')
    formula = models.TextField(blank=True, verbose_name='Formula')
    receivers = models.TextField(blank=True, verbose_name="Receivers")
    wiki_link = models.URLField(blank=True, verbose_name="WiKi")
    device = models.CharField(max_length=255, blank=True, verbose_name="PyAlarm device")
    is_disabled = models.BooleanField(default=False, verbose_name="Disabled")
    is_active = models.BooleanField(default=False, verbose_name="Active")
    activation_time = models.DateTimeField(blank=True, verbose_name="Activation time", null=True)

# check if SNAP is available
try:
    db = alarmapi._TANGO #fandango.get_database()
    assert list(db.get_device_exported_for_class('SnapManager'))
    snap_api = snap.SnapAPI()
except Exception, e:
    logging.warning('PyTangoArchiving.Snaps not available: '
                    'History synchronization is disabld: \n %s \n' % e.message)
    snap_api = None


class AlarmHistoryQueryset(models.QuerySet):
    """Queryset to manage alarm history SNAP database."""

    def updated(self):
        """Returns a queryset after database synchronization"""

        if snap_api is None:
            return self

        try:
            # iterate through defined alarms and do update
            for alarm in AlarmModel.objects.all():

                # find SNAP context for alarm
                alarm_ctx = snap_api.get_context(name=alarm.tag)

                if alarm_ctx is not None:
                    # check timestamp of the latest synchronized snapshot
                    if alarm.history.count() > 0:
                        last_update_time = alarm.history.latest('date')
                    else:
                        last_update_time = datetime.fromtimestamp(0)
                    # retrieve new snapshots from the database
                    snaps = alarm_ctx.db.get_context_snapshots(context_id=alarm_ctx.ID, dates=(last_update_time, datetime.now()))

                    # iterate through new snapshots and create objects
                    for snapshot in snaps:

                        # find object in a database
                        alarm_history, is_created = AlarmHistoryModel.objects.get_or_create(alarm=alarm,
                                                                                            date=snapshot[1],
                                                                                            comment=snapshot[2])
                        assert isinstance(alarm_history, AlarmHistoryModel)

                        # set fields
                        alarm_history.alarm = alarm
                        alarm_history.date = snapshot[1]
                        alarm_history.comment = snapshot[2]

                        # save to database
                        alarm.save()
        except OperationalError as oe:
            logger.warning('There is an operational error: %s \n'
                           'If it is before any migration it is normal for .updated() method '
                           'tries to use a table which is not yet created.' % str(oe))

        return self


class AlarmHistoryModel(models.Model):

    # set custom manager based on custom queryset
    objects = AlarmHistoryQueryset.as_manager()

    # fields
    alarm = models.ForeignKey(AlarmModel, related_name='history')
    date = models.DateTimeField()
    comment = models.TextField()



