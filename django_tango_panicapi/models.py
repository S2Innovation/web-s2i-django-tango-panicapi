# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import OperationalError
from django.utils import timezone, dateparse
from django.utils.dateparse import parse_datetime
from panic import alarmapi
from PyTangoArchiving import snap
from datetime import datetime, timedelta
import logging
from threading import RLock

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
alarms = None
snap_api = None
api_loc= RLock()

def prepare_api():
    """Prepare api opbjects"""
    global alarms
    global snap_api
    global api_loc
    with api_loc:
        if alarms is None:
            alarms = alarmapi.api()
        # check if SNAP is available
        if snap_api is None:
            try:
                db = alarmapi._TANGO  # fandango.get_database()
                assert list(db.get_device_exported_for_class('SnapManager'))
                snap_api = snap.SnapAPI()
            except Exception, e:
                logging.warning('PyTangoArchiving.Snaps not available: '
                                'History synchronization is disabld: \n %s \n' % e.message)
                snap_api = None


class AlarmsApiSettingsModel(models.Model):
    """Model to keep settings for the application"""
    last_alarms_update = models.DateTimeField(
        default=datetime.fromtimestamp(0), #, timezone.get_current_timezone()),
        verbose_name='Last alarms update',
    )
    last_history_update = models.DateTimeField(
        default=datetime.fromtimestamp(0), #timezone.get_current_timezone()),
        verbose_name='Last history update',
    )
    update_period = models.DurationField(
        default=timedelta(seconds=5),
        verbose_name='Database update period',
    )


class AlarmQueryset(models.QuerySet):
    """Queryset to manage alarm database."""

    def updated(self):
        """Returns a queryset after database synchronization"""

        global alarms
        global api_loc
        # iterate through defined alarms and do update
        try:
            if AlarmsApiSettingsModel.objects.count() > 0:
                api_settings = AlarmsApiSettingsModel.objects.last()
            else:
                api_settings = AlarmsApiSettingsModel(
                    last_alarms_update=datetime.fromtimestamp(0, timezone.get_current_timezone()),
                    last_history_update=datetime.fromtimestamp(0, timezone.get_current_timezone()),
                    update_period=timedelta(seconds=5)
                )

            # avoid too often updates
            if timezone.now() - api_settings.last_alarms_update < api_settings.update_period:
                return self

            api_settings.last_alarms_update = timezone.now()
            api_settings.save()

            prepare_api()

            for alarm_tag in alarms.keys():
                # find object in a database
                alarm, is_created = AlarmModel.objects.get_or_create(tag=alarm_tag)
                assert isinstance(alarm, AlarmModel)

                # set fields
                with api_loc:
                    panic_alarm = alarms[alarm_tag]
                assert isinstance(panic_alarm, Alarm)
                alarm.tag = alarm_tag
                alarm.severity = panic_alarm.get_priority()
                alarm.is_disabled = panic_alarm.get_enabled(force=True)
                panic_alarm.get_acknowledged(force=True)
                panic_alarm.set_active(panic_alarm.get_time(True))
                if panic_alarm.time != 0:
                    alarm.activation_time = timezone.get_current_timezone().localize(datetime.fromtimestamp(panic_alarm.time))
                else:
                    alarm.activation_time = None
                alarm.state = panic_alarm.get_state(force=True)
                alarm.description = panic_alarm.description
                alarm.formula = panic_alarm.get_condition()
                alarm.receivers = panic_alarm.get_annunciators()
                try:
                    alarm.wiki_link = panic_alarm.get_wiki_link()
                except AttributeError:
                    alarm.wiki_link = ''

                alarm.is_active = (panic_alarm.is_active() > 0)
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




class AlarmHistoryQueryset(models.QuerySet):
    """Queryset to manage alarm history SNAP database."""

    def updated(self):
        """Returns a queryset after database synchronization"""

        global snap_api
        global alarms
        global api_loc

        try:

            if AlarmsApiSettingsModel.objects.count() > 0:
                api_settings = AlarmsApiSettingsModel.objects.last()
            else:
                api_settings = AlarmsApiSettingsModel(
                    last_alarms_update=datetime.fromtimestamp(0, timezone.get_current_timezone()),
                    last_history_update=datetime.fromtimestamp(0, timezone.get_current_timezone()),
                    update_period=timedelta(seconds=5)
                )

            # avoid too often updates
            if timezone.now() - api_settings.last_history_update < api_settings.update_period:
              return self

            api_settings.last_history_update = timezone.now()
            api_settings.save()

            prepare_api()
            with api_loc:
                if snap_api is None:
                    return self

            try:
                # iterate through defined alarms and do update
                for alarm in AlarmModel.objects.all():
                    if snap_api is None:
                        prepare_api()
                    # find SNAP context for alarm
                    with api_loc:
                        alarm_ctx = snap_api.get_context(name=alarm.tag)

                    if alarm_ctx is not None:

                        try:
                            # retrieve new snapshots from the database
                            with api_loc:
                                snaps = alarm_ctx.db.get_context_snapshots(context_id=alarm_ctx.ID, limit=50) # =(last_update_time-timedelta(days=1), timezone.now()+timedelta(days=1)))

                            # iterate through new snapshots and create objects
                            for snapshot in snaps:

                                # print snapshot[1]

                                # find object in a database
                                alarm_history, is_created = AlarmHistoryModel.objects.get_or_create(
                                    alarm=alarm,
                                    date=timezone.get_current_timezone().localize(
                                        dateparse.parse_datetime(str(snapshot[1]))
                                    ),
                                    comment=snapshot[2]
                                )
                                assert isinstance(alarm_history, AlarmHistoryModel)

                                if is_created:
                                    # set fields
                                    alarm_history.alarm = alarm
                                    alarm_history.date = timezone.get_current_timezone().localize(dateparse.parse_datetime(str(snapshot[1])))
                                    alarm_history.comment = snapshot[2]
                                    # save to database
                                    alarm.save()
                        except Exception as ce:
                            logger.warning('There is an errot in reading context history: %s \n' % str(ce))
                            snap_api = None

            except:
                # if there is an issue here it is usally due to snap db...
                snap_api = None


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



