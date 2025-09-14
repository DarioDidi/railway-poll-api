# polls/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Poll, Vote


class PollCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating polls with validation for start and expiry dates.
    """
    class Meta:
        model = Poll
        fields = [
            'question', 'options', 'is_anonymous',
            'start_date', 'expiry_date'
        ]

    def validate(self, data):
        start_date = data.get('start_date', timezone.now())
        expiry_date = data.get('expiry_date')

        if expiry_date <= start_date:
            raise serializers.ValidationError(
                "Expiry date must be after start date."
            )

        min_expiry = start_date + timezone.timedelta(hours=1)
        if expiry_date < min_expiry:
            raise serializers.ValidationError(
                "Poll must be active for at least 1 hour."
            )

        max_expiry = start_date + timezone.timedelta(days=7)
        if expiry_date > max_expiry:
            raise serializers.ValidationError(
                "Poll cannot be active for more than 7 days."
            )

        return data


class PollSerializer(serializers.ModelSerializer):
    """
    Serializer for reading poll data with computed fields.
    """
    creator_email = serializers.EmailField(
        source='creator.email', read_only=True)
    total_votes = serializers.IntegerField(read_only=True)
    has_user_voted = serializers.BooleanField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Poll
        fields = [
            'id', 'question', 'options', 'is_anonymous', 'created_at',
            'updated_at', 'creator_email', 'start_date', 'expiry_date',
            'is_active', 'total_votes', 'has_user_voted', 'status'
        ]


class VoteSerializer(serializers.ModelSerializer):
    """
    Serializer for casting votes with validation.
    """
    class Meta:
        model = Vote
        fields = ['option_index']

    def __init__(self, *args, **kwargs):
        self.poll = kwargs.pop('context', {}).get('poll')
        self.request = kwargs.pop('context', {}).get('request')
        super().__init__(*args, **kwargs)

    def validate_option_index(self, value):
        if not self.poll or value >= len(self.poll.options):
            raise serializers.ValidationError("Invalid option index.")
        return value

    def validate(self, data):
        if not self.poll.can_vote():
            raise serializers.ValidationError(
                "This poll is not currently active.")

        # Check for existing vote
        user = self.request.user if self.request.user.is_authenticated else None
        ip_address = self.request.META.get(
            'REMOTE_ADDR') if self.request else None

        existing_vote = Vote.objects.filter(
            poll=self.poll,
            user=user
        ).exists()

        if existing_vote:
            raise serializers.ValidationError(
                "You have already voted on this poll.")

        return data

    def save(self, **kwargs):
        vote = Vote(
            poll=self.poll,
            user=self.request.user if self.request.user.is_authenticated
            else None,
            option_index=self.validated_data['option_index'],
            ip_address=self.request.META.get(
                'REMOTE_ADDR') if self.request else None
        )
        vote.save()
        return vote


class PollResultsSerializer(serializers.Serializer):
    """
    Serializer for poll results with vote counts and percentages.
    """
    results = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField())
    )


class UserVoteSerializer(serializers.ModelSerializer):
    """
    Serializer for user's own votes
    """
    poll_question = serializers.CharField(
        source='poll.question', read_only=True)
    poll_id = serializers.UUIDField(source='poll.id', read_only=True)
    selected_option = serializers.SerializerMethodField()

    class Meta:
        model = Vote
        fields = ['id', 'poll_id', 'poll_question',
                  'selected_option', 'created_at']

    def get_selected_option(self, obj):
        """Get the actual option text that was voted for"""
        if obj.option_index < len(obj.poll.options):
            return obj.poll.options[obj.option_index]
        return "Unknown option"
