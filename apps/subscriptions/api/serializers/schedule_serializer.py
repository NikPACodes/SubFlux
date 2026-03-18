from rest_framework import serializers

from utils.enums import PeriodUnit
from utils.validators import validate_billing_schedule_params


class ScheduleInputSerializer(serializers.Serializer):
    """
    Сериализатор для расчета списаний по подписке
    """
    period_unit = serializers.ChoiceField(choices=PeriodUnit)
    period_interval = serializers.IntegerField(default=1)
    anchor_day = serializers.IntegerField(required=False, allow_null=True)
    anchor_weekday = serializers.IntegerField(required=False, allow_null=True)
    trial_ends_at = serializers.DateTimeField(required=False, allow_null=True)
    grace_days = serializers.IntegerField(default=0)

    def validate(self, attrs):
        try:
            validate_billing_schedule_params(
                period_unit=attrs.get('period_unit'),
                period_interval=attrs.get('period_interval'),
                anchor_day=attrs.get('anchor_day'),
                anchor_weekday=attrs.get('anchor_weekday'),
                grace_days=attrs.get('grace_days'),
            )
        except ValueError as e:
            raise serializers.ValidationError(str(e))

        return  attrs
