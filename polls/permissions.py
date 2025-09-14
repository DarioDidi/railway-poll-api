# polls/permissions.py
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    Read permissions are allowed to any request.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class CanVote(permissions.BasePermission):
    """
    Permission to check if a user can vote on a specific poll.
    Now only checks poll status since voting is always authenticated.
    """

    def has_object_permission(self, request, view, obj):
        # Check if poll is active
        if not obj.can_vote():
            raise PermissionDenied(
                detail="This poll is not currently accepting votes.",
                code='poll_inactive'
            )

        # Check for existing vote by this user
        existing_vote = obj.votes.filter(user=request.user).exists()
        if existing_vote:
            raise PermissionDenied(
                detail="You have already voted on this poll.",
                code='already_voted'
            )

        return True


class IsPollOwner(permissions.BasePermission):
    """
    Permission that only allows the owner of a poll to perform actions.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class CanEditPoll(permissions.BasePermission):
    """
    Permission to check if a poll can be edited.
    Prevents editing after a poll has started accepting votes.
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is owner and poll hasn't started yet
        if obj.owner != request.user:
            return False

        # Check if poll has already started
        if obj.has_started:
            raise PermissionDenied(
                detail="Cannot edit poll after it has started accepting votes",
                code='poll_started'
            )

        return True
