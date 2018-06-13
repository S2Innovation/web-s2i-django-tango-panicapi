from rest_framework import serializers
from models import *


class AlarmSerializer(serializers.ModelSerializer):

    class Meta:
        model = AlarmModel
        fields = (
            'tag',
            'severity',
            'state',
            'description',
            'formula',
            'receivers',
            'wiki_link',
            'device',
            'is_active',
            'is_disabled',
            'activation_time'
        )

class AlarmShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = AlarmModel
        fields = (
            'tag',
            'severity',
        )


class AlarmHistorySerializer(serializers.ModelSerializer):

    alarm = AlarmShortSerializer()

    class Meta:
        model = AlarmHistoryModel
        fields = (
            'id',
            'alarm',
            # 'alarm_tag',
            'date',
            'comment',
        )
