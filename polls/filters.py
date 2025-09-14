# polls/filters.py
# import django_filters
from django_filters import rest_framework as filters
from django.utils import timezone
from .models import Poll


class PollFilter(filters.FilterSet):
    """
    Advanced filtering for polls with date ranges and search capabilities.
    """
    question = filters.CharFilter(lookup_expr='icontains')
    creator_email = filters.CharFilter(
        field_name='creator__email', lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_anonymous = filters.BooleanFilter()

    created_after = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(
        field_name='created_at', lookup_expr='lte')

    expires_after = filters.DateTimeFilter(
        field_name='expiry_date', lookup_expr='gte')
    expires_before = filters.DateTimeFilter(
        field_name='expiry_date', lookup_expr='lte')

    status = filters.ChoiceFilter(
        choices=[
            ('active', 'Active'),
            ('upcoming', 'Upcoming'),
            ('expired', 'Expired')
        ],
        method='filter_by_status'
    )

    class Meta:
        model = Poll
        fields = [
            'question', 'creator_email', 'is_active', 'is_anonymous',
            'created_after', 'created_before',
            'expires_after', 'expires_before',
            'status'
        ]

    def filter_by_status(self, queryset, name, value):
        """
        Custom filter for poll status (active, upcoming, expired).
        """
        now = timezone.now()

        if value == 'active':
            return queryset.filter(
                start_date__lte=now,
                expiry_date__gte=now,
                is_active=True
            )
        elif value == 'upcoming':
            return queryset.filter(
                start_date__gt=now,
                is_active=True
            )
        elif value == 'expired':
            return queryset.filter(
                expiry_date__lt=now
            )

        return queryset
