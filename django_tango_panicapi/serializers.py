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

class AlarmHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = AlarmHistoryModel
        fields = (
            'id',
            'date',
            'comment',
        )
