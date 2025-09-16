import pytest
from django.utils import timezone
import json
from rest_framework import status
from django.urls import reverse
from polls.models import Poll, Vote


@pytest.mark.django_db
class TestPollAPI:
    """Test cases for Poll API endpoints"""

    def test_create_poll_authenticated(self, authenticated_client, user):
        """Test creating a poll as an authenticated user"""
        url = reverse('poll-list')
        start_date = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        expiry_date = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        data = {
            'question': 'New Test Poll?',
            'options': ['Choice 1', 'Choice 2', 'Choice 3'],
            'is_anonymous': False,
            'start_date': start_date,
            'expiry_date': expiry_date
        }

        response = authenticated_client.post(url, data, format='json')

        if response.status_code != 201:
            print("Error response:", json.dumps(response.data, indent=2))
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['question'] == data['question']

        assert response.data['owner_email'] == user.email
        assert response.data['creator_email'] == user.email

    def test_create_anonymous_poll(self, authenticated_client, user):
        """Test creating an anonymous poll"""
        url = reverse('poll-list')
        start_date = (timezone.now() + timezone.timedelta(hours=1)).isoformat()
        expiry_date = (timezone.now() + timezone.timedelta(days=1)).isoformat()
        data = {
            'question': 'Anonymous Poll?',
            'options': ['Yes', 'No'],
            'is_anonymous': True,
            'start_date': start_date,
            'expiry_date': expiry_date
        }

        response = authenticated_client.post(url, data, format='json')
        # print("Response data:", response.data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_anonymous'] is True
        assert response.data['creator_email'] is None

    def test_create_poll_unauthenticated(self, client):
        """Test that unauthenticated users cannot create polls"""
        url = reverse('poll-list')
        data = {
            'question': 'Unauthenticated Poll?',
            'options': ['Yes', 'No']
        }

        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_vote_on_poll(self, authenticated_client, poll, user):
        """Test voting on a poll"""
        vote_url = reverse('poll-vote', kwargs={'pk': poll.id})
        data = {'option_index': 1}

        response = authenticated_client.post(vote_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Vote.objects.filter(poll=poll, user=user).count() == 1
        assert Vote.objects.first().option_index == 1

    def test_duplicate_vote_prevention(self, authenticated_client, poll, user):
        """Test that users cannot vote multiple times on the same poll"""
        vote_url = reverse('poll-vote', kwargs={'pk': poll.id})
        data = {'option_index': 0}

        # First vote should succeed
        response1 = authenticated_client.post(vote_url, data, format='json')
        assert response1.status_code == status.HTTP_201_CREATED

        # Second vote should fail
        response2 = authenticated_client.post(vote_url, data, format='json')
        print("Response data:", response2.data)
        print("Response status:", response2.status_code)
        assert response2.status_code == status.HTTP_403_FORBIDDEN
        # assert 'already voted' in
        # response2.data['non_field_errors'][0].lower()

    def test_vote_unauthenticated(self, client, poll):
        """Test that unauthenticated users cannot vote"""
        vote_url = reverse('poll-vote', kwargs={'pk': poll.id})
        data = {'option_index': 0}

        response = client.post(vote_url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_poll_results_unauthenticated(self, client, poll_with_votes):
        """Test that anyone can view poll results"""
        results_url = reverse(
            'poll-results', kwargs={'pk': poll_with_votes.id})

        response = client.get(results_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == len(poll_with_votes.options)

    def test_my_polls_endpoint(self, authenticated_client, user, poll, anonymous_poll):
        """Test that users can see all polls they own"""
        my_polls_url = reverse('poll-my-polls')

        response = authenticated_client.get(my_polls_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2  # Both regular and anonymous polls

    def test_edit_poll_before_start(self, authenticated_client, future_poll):
        """Test editing a poll before it starts"""
        url = reverse('poll-detail', kwargs={'pk': future_poll.id})
        data = {'question': 'Updated Question'}

        response = authenticated_client.patch(url, data, format='json')
        print(response.data)
        assert response.status_code == status.HTTP_200_OK

    def test_edit_poll_after_start(self, authenticated_client, poll):
        """Test that editing is blocked after poll starts"""
        url = reverse('poll-detail', kwargs={'pk': poll.id})
        data = {'question': 'Updated Question'}

        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
