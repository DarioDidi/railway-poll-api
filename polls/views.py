
# polls/views.py
from .filters import PollFilter
from .permissions import (
    # IsOwnerOrReadOnly,
    CanVote,
    CanEditPoll,
    CanDeletePoll,
    # IsAuthenticatedForWriteOperations,
    CanViewOwnVotes,
    VotesAreReadOnly
)
from .serializers import (
    PollSerializer,
    VoteSerializer,
    PollResultsSerializer,
    PollCreateSerializer,
    UserVoteSerializer
)
from rest_framework import viewsets, status, mixins
from rest_framework import filters as rest_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.decorators import method_decorator

from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# realtime updates
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Poll, Vote


import logging

logger = logging.getLogger(__name__)


@method_decorator(name='destroy', decorator=swagger_auto_schema(
    operation_description="Delete a poll"
))
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

    @swagger_auto_schema(
        operation_description="Create a new poll",
        request_body=PollCreateSerializer,
        responses={
            201: PollSerializer,
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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
            # permission_classes = [IsOwnerOrReadOnly]
            permission_classes = [AllowAny,]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        instance = serializer.save()
        # Trigger real-time notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'polls_list',
            {
                'type': 'poll_created',
                'data': {
                    'id': str(instance.id),
                    'question': instance.question,
                    'created_at': instance.created_at.isoformat(),
                    'owner_email': instance.owner.email
                }
            }
        )

    def perform_destroy(self, instance):
        """Override to trigger real-time updates"""
        poll_id = str(instance.id)
        super().perform_destroy(instance)

        # Trigger real-time notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'polls_list',
            {
                'type': 'poll_deleted',
                'data': {
                    'id': poll_id,
                    'timestamp': timezone.now().isoformat()
                }
            }
        )

    @swagger_auto_schema(
        operation_description=("Retrieve a list of polls"
                               "with filtering options"),
        manual_parameters=[
            openapi.Parameter(
                'question',
                openapi.IN_QUERY,
                description="Filter by question text (contains)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'creator_email',
                openapi.IN_QUERY,
                description="Filter by creator_email (contains)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (active, upcoming, expired)",
                type=openapi.TYPE_STRING,
                enum=['active', 'upcoming', 'expired']
            ),
            openapi.Parameter(
                'created_after',
                openapi.IN_QUERY,
                description="Filter polls created after this date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
            openapi.Parameter(
                'created_before',
                openapi.IN_QUERY,
                description="Filter polls created before this date",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Cast a vote on a specific poll",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'option_index': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Index of the selected option (0-based)"
                )
            }
        ),
        responses={
            201: "Vote recorded successfully",
            400: "Bad Request - Invalid option or already voted",
            404: "Poll not found"
        }
    )
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """
        Cast a vote on a specific poll (authenticated users only).
        """
        poll = self.get_object()
        print("on poll", poll)
        serializer = VoteSerializer(
            data=request.data,
            context={'poll': poll, 'request': request}
        )

        if serializer.is_valid():
            print("Serializer  VALID")
            vote = serializer.save()

            # Trigger real-time updates via signal (already handled)
            # Additional real-time notification if needed
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'poll_{poll.id}',
                {
                    'type': 'poll_update',
                    'data': {
                        'type': 'vote_cast',
                        'poll_id': str(poll.id),
                        'results': poll.get_results(),
                        'total_votes': poll.votes.count(),
                        'timestamp': vote.created_at.isoformat()
                    }
                }
            )

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


class VoteViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    ViewSet for users to view their own votes.
    Votes are permanent and cannot be modified or deleted.
    Votes are created through poll vote endpoint
    """
    serializer_class = UserVoteSerializer
    permission_classes = [IsAuthenticated, VotesAreReadOnly, CanViewOwnVotes]

    def get_queryset(self):
        """Users can only see their own votes"""
        # Short-circuit during Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Vote.objects.none()

        # Allow admins to see all votes
        if self.request.user.is_staff:
            return Vote.objects.all()

        # Handle both authenticated and unauthenticated users
        if hasattr(self.request.user, 'is_authenticated') \
                and self.request.user.is_authenticated:
            return Vote.objects.filter(user=self.request.user)
        return Vote.objects.none()

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


@action(detail=True, methods=['get'])
def export_results(self, request, pk=None):
    """
    Export poll results in various formats (JSON, CSV, Excel).
    """
    poll = self.get_object()
    format = request.GET.get('format', 'json')

    results = poll.get_results()

    if format == 'csv':
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="poll_{poll.id}_results.csv"'

        writer = csv.writer(response)
        writer.writerow(['Option', 'Votes', 'Percentage'])

        for result in results:
            writer.writerow([
                result['option'],
                result['votes'],
                f"{result['percentage']:.2f}%"
            ])

        return response

    elif format == 'json':
        return Response({
            'poll': {
                'id': str(poll.id),
                'question': poll.question,
                'total_votes': sum(result['votes'] for result in results)
            },
            'results': results,
            'exported_at': timezone.now()
        })

    else:
        return Response(
            {'error': 'Unsupported format. Use "json" or "csv".'},
            status=status.HTTP_400_BAD_REQUEST
        )
