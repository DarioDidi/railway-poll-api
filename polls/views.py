
# Create your views here.
from rest_framework import viewsets, status, mixins
from rest_framework import filters as rest_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

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
    # IsAuthenticatedForWriteOperations,
    CanViewOwnVotes,
    VotesAreReadOnly
)
from .filters import PollFilter


class PollViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing polls with comprehensive permission controls.
    """
    queryset = Poll.objects.all()
    filter_backends = [
        DjangoFilterBackend,
        rest_filters.SearchFilter,
        rest_filters.OrderingFilter
    ]
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

    def get_permissions(self):
        """
        Assign appropriate permissions based on the action.
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, CanEditPoll]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, CanDeletePoll]
        elif self.action == 'vote':
            permission_classes = [IsAuthenticated, CanVote]
        else:
            # list, retrieve, results - read operations
            permission_classes = [IsOwnerOrReadOnly]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """
        Cast a vote on a specific poll (authenticated users only).
        """
        print("\n\n\nVOTINNG\n\n")
        poll = self.get_object()
        print("on poll", poll)
        serializer = VoteSerializer(
            data=request.data,
            context={'poll': poll, 'request': request}
        )

        if serializer.is_valid():
            print("Serializer  VALID")
            serializer.save()
            return Response(
                {'message': 'Vote recorded successfully'},
                status=status.HTTP_201_CREATED
            )
        print("Serializer NOT VALID")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get real-time results for a specific poll
        """
        poll = self.get_object()
        results = poll.get_results()
        serializer = self.get_serializer({'results': results})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active polls (current time between start and expiry dates).
        """
        now = timezone.now()
        active_polls = Poll.objects.filter(
            start_date__lte=now,
            expiry_date__gte=now,
            is_active=True
        )
        page = self.paginate_queryset(active_polls)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_polls(self, request):
        """
        Get all active polls (current time between start and expiry dates).
        """
        user_polls = Poll.objects.filter(
            owner=self.request.user
        )
        page = self.paginate_queryset(user_polls)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# class VoteViewSet(mixins.ListModelMixin,
        # mixins.RetrieveModelMixin,
        # viewsets.GenericViewSet):


class VoteViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    ViewSet for users to view their own votes.
    Votes are permanent and cannot be modified or deleted.
    Votes are created through poll vote endpoint
    """
    serializer_class = UserVoteSerializer
    # permission_classes = [IsAuthenticated, CanViewOwnVotes, VotesAreReadOnly]

    # REORDER: Method-level permission first, then object-level
    permission_classes = [IsAuthenticated, VotesAreReadOnly, CanViewOwnVotes]

    def get_queryset(self):
        """Users can only see their own votes"""
        return Vote.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_poll(self, request):
        """
        Get all votes by the current user for a specific poll.
        """
        poll_id = request.query_params.get('poll_id')
        if not poll_id:
            return Response(
                {'error': 'poll_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            votes = Vote.objects.filter(
                user=request.user,
                poll_id=poll_id
            )
            serializer = self.get_serializer(votes, many=True)
            return Response(serializer.data)
        except (ValueError, ValidationError):
            return Response(
                {'error': 'Invalid poll_id format'},
                status=status.HTTP_400_BAD_REQUEST
            )
