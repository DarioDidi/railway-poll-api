import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from users.models import User


class Poll(models.Model):
    """
    Represents a poll/survey with multiple options and voting constraints.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField(max_length=500)
    options = models.JSONField()  # Stores list of option strings
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_polls'
    )
    expiry_date = models.DateTimeField(
        validators=[MinValueValidator(
            timezone.now() + timezone.timedelta(hours=1))]
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        validators=[MinValueValidator(timezone.now())]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['creator', 'created_at']),
            models.Index(fields=['expiry_date', 'is_active']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.question[:50]}... by {self.creator.email}"

    @property
    def has_started(self):
        return timezone.now() >= self.start_date

    @property
    def has_ended(self):
        return timezone.now() >= self.expiry_date

    def can_vote(self):
        return self.has_started and not self.has_ended and self.is_active

    def get_results(self):
        """Calculate real-time results with caching consideration"""
        from django.core.cache import cache
        cache_key = f"poll_results_{self.id}"
        results = cache.get(cache_key)

        if not results:
            results = []
            for index, option in enumerate(self.options):
                vote_count = self.votes.filter(option_index=index).count()
                results.append({
                    'option': option,
                    'votes': vote_count,
                    'percentage': (vote_count / self.votes.count() * 100)
                    if self.votes.count() > 0 else 0
                })
            # Cache for 5 minutes for active polls, longer for ended polls
            cache_timeout = 300 if self.can_vote() else 3600
            cache.set(cache_key, results, cache_timeout)

        return results


class Vote(models.Model):
    """
    Records a user's vote on a specific poll option.
    Implements unique constraint to prevent duplicate voting.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    option_index = models.IntegerField(
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['poll', 'user'],
                name='unique_user_vote',
                condition=models.Q(user__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['poll', 'ip_address'],
                name='unique_ip_vote',
                condition=models.Q(user__isnull=True, ip_address__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['poll', 'user']),
            models.Index(fields=['poll', 'ip_address']),
        ]

    def __str__(self):
        voter = self.user.email if self.user else self.ip_address
        return f"Vote by {voter} on {self.poll.question[:30]}..."


class BlockedIP(models.Model):
    """
    Stores IP addresses that are blocked due to suspicious activity.
    """
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.ip_address} - {self.reason[:50]}..."
