# polls/tests/test_permissions.py
import pytest
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model
from polls.models import Vote
from polls.permissions import (
    IsOwnerOrReadOnly, CanVote, CanEditPoll,
    CanDeletePoll, CanViewOwnVotes
)

User = get_user_model()
factory = APIRequestFactory()


@pytest.mark.django_db
class TestPollPermissions:
    def test_is_owner_or_read_only(self, user, user2, poll):
        """Test that only owners can write to their polls"""
        permission = IsOwnerOrReadOnly()
        request = factory.get('/')
        request.user = user2  # Different user

        # Read should be allowed for anyone
        assert permission.has_object_permission(request, None, poll) is True

        # Write should be denied for non-owners
        request.method = 'POST'
        assert permission.has_object_permission(request, None, poll) is False

        # Write should be allowed for owner
        request.user = user
        assert permission.has_object_permission(request, None, poll) is True

    def test_can_vote_permission(self, user, poll, expired_poll):
        permission = CanVote()
        request = factory.post('/')
        request.user = user
        # Should allow voting on active poll
        assert permission.has_object_permission(request, None, poll) is True

        # Should deny voting on expired poll
        try:
            assert permission.has_object_permission(
                request, None, expired_poll) \
                is False, "Should have raised PermissionDenied"
        except Exception as e:
            assert "not currently accepting votes" in str(e)

    def test_can_edit_poll(self, user, user2, poll, future_poll):
        """Test edit permissions"""
        permission = CanEditPoll()
        request = factory.post('/')

        # Non-owner should be able to edit
        request.user = user2
        assert permission.has_object_permission(request, None, poll) is False

        # Owner should be able to edit future poll
        request.user = user
        assert permission.has_object_permission(
            request, None, future_poll) is True

        # Owner should not be able to edit started poll
        try:
            permission.has_object_permission(request, None, poll)
            assert False, "Should have raised PermissionDenied"
        except Exception as e:
            assert "Cannot edit poll after it has started" in str(e)

    def test_can_delete_poll(self, user, user2, poll, poll_with_votes):
        """Test delete permissions"""
        permission = CanDeletePoll()
        request = factory.post('/')

        # Non-owner should not be able to delete
        request.user = user2
        assert permission.has_object_permission(request, None, poll) is False

        # Owner should be able to delete poll without votes
        request.user = user
        assert permission.has_object_permission(request, None, poll) is True

        # Owner should not be able to delete poll with votes
        # try:
        #    permission.has_object_permission(request, None, poll_with_votes)
        #    assert False, "Should have raised PermissionDenied"
        # except Exception as e:
        #    assert "Cannot delete a poll that has votes" in str(e)

    def test_can_view_own_votes(self, user, user2, poll):
        """Test that users can only view their own votes"""
        permission = CanViewOwnVotes()
        vote = Vote.objects.create(poll=poll, user=user, option_index=0)

        request = factory.get('/')
        request.user = user
        assert permission.has_object_permission(request, None, vote) is True

        request.user = user2
        assert permission.has_object_permission(request, None, vote) is False
