
# Create your views here.
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
        poll = self.get_object()
        serializer = VoteSerializer(
            data=request.data,
            context={'poll': poll, 'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Vote recorded successfully'},
                status=status.HTTP_201_CREATED
            )
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


class VoteViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):

    """
    ViewSet for users to manage their own votes.
    Users can view and delete their votes, but not create/update.
    Voting isdone via Poll vote action
    """
    serializer_class = UserVoteSerializer
    permission_classes = [IsAuthenticated, CanViewOwnVotes]
    http_method_names = [
        m for m in viewsets.ModelViewSet.http_method_names
        if m not in ['delete']
    ]

    def get_queryset(self):
        """Users can only see their own votes"""
        return Vote.objects.filter(user=self.request.user)

    def destroy(self, request, pk=None):
        response = {'message': 'Delete function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)
