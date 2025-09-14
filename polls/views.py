
# Create your views here.
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Poll, Vote
from .serializers import (
    PollSerializer,
    VoteSerializer,
    PollResultsSerializer,
    PollCreateSerializer,
    UserVoteSerializer
)
from .permissions import (
    IsOwnerOrReadOnly,
    CanVote,
    CanEditPoll,
    CanDeletePoll,
    IsAuthenticatedForWriteOperations,
    CanViewOwnVotes
)
from .filters import PollFilter


class PollViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing polls with comprehensive permission controls.
    """
    queryset = Poll.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = PollFilter
    search_fields = ['question', 'owner__email']
    ordering_fields = ['created_at', 'updated_at', 'start_date', 'expiry_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PollCreateSerializer
        elif self.action == 'results':
            return PollResultsSerializer
        return PollSerializer
