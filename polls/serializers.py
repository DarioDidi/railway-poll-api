# polls/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import Poll, Vote

from polls.models import current_time


class PollCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating polls with validation for start and expiry dates.
    """
    owner_email = serializers.SerializerMethodField()
    creator_email = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = [
            'question', 'options', 'is_anonymous',
            'start_date', 'expiry_date',
            'owner_email', 'creator_email'
        ]

    def validate(self, data):
        def_start = current_time()
        def_end = def_start + timezone.timedelta(days=7)
        start_date = data.get('start_date', def_start)
        expiry_date = data.get('expiry_date', def_end)

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

    def create(self, validated_data):
        """
        Create poll, setting owner to current user and creator
        based on anonymity.
        """
        request = self.context.get('request')
        user = request.user

        # Set owner to current user
        validated_data['owner'] = user

        # Set creator to user only if poll is not anonymous
        if not validated_data.get('is_anonymous', False):
            validated_data['creator'] = user

        return super().create(validated_data)

    def get_owner_email(self, obj):
        """Always show owner email (accountability)"""
        return obj.owner.email

    def get_creator_email(self, obj):
        """Show creator email only for non-anonymous polls"""
        if not obj.is_anonymous and obj.creator:
            return obj.creator.email
        return None


class PollSerializer(serializers.ModelSerializer):
    """
    Serializer for reading poll data with computed fields.
    Shows owner email only for non-anonymous polls.
    """
    owner_email = serializers.SerializerMethodField()
    creator_email = serializers.SerializerMethodField()
    total_votes = serializers.IntegerField(read_only=True)
    has_user_voted = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Poll
        fields = [
            'id', 'question', 'options', 'is_anonymous', 'created_at',
            'updated_at', 'owner_email', 'creator_email', 'start_date',
            'expiry_date', 'is_active', 'total_votes',
            'has_user_voted', 'status'
        ]

    def get_owner_email(self, obj):
        """Always show owner email (accountability)"""
        return obj.owner.email

    def get_creator_email(self, obj):
        """Show creator email only for non-anonymous polls"""
        if not obj.is_anonymous and obj.creator:
            return obj.creator.email
        return None

    def get_has_user_voted(self, obj):
        """Check if current user has voted on this poll"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.votes.filter(user=request.user).exists()
        return False


class VoteSerializer(serializers.ModelSerializer):
    """
    Serializer for casting votes with validation.
    """
    class Meta:
        model = Vote
        fields = ['option_index']

    def __init__(self, *args, **kwargs):
        self.poll = kwargs.get('context', {}).get('poll')
        self.request = kwargs.get('context', {}).get('request')
        print("REQUEST:", self.request)
        super().__init__(*args, **kwargs)

    def validate_option_index(self, value):
        if not self.poll or value >= len(self.poll.options):
            raise serializers.ValidationError("Invalid option index.")
        return value

    def validate(self, data):
        print("validation poll")
        if not self.poll.can_vote():
            raise serializers.ValidationError(
                "This poll is not currently active.")

        # Check for existing vote
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            None

        existing_vote = Vote.objects.filter(
            poll=self.poll,
            user=user
        ).exists()

        print("checking exisiting vote for user:",
              user, "exists:", existing_vote)
        if existing_vote:
            print("RAISING ALREADY VOTED ERROR")
            raise serializers.ValidationError(
                "You have already voted on this poll.")

        return data

    def save(self, **kwargs):
        vote = Vote(
            poll=self.poll,
            user=self.request.user if self.request.user.is_authenticated
            else None,
            option_index=self.validated_data['option_index'],
        )
        vote.save()
        print("serializer creating vote:", vote)
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
