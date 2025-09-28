import pytest
from rest_framework import status
from django.urls import reverse


denied_status = [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
class TestAuthenticationRequirements:
    """Test authentication requirements for different endpoints"""

    def test_public_read_access(self, client, poll):
        """Test that read operations are public"""
        # List polls
        response = client.get(reverse('poll-list'))
        print(f"polls-list resp:{response}")
        assert response.status_code == status.HTTP_200_OK

        # Retrieve single poll
        response = client.get(reverse('poll-detail', kwargs={'pk': poll.id}))
        assert response.status_code == status.HTTP_200_OK

        # Get results
        response = client.get(reverse('poll-results', kwargs={'pk': poll.id}))
        assert response.status_code == status.HTTP_200_OK

    def test_authenticated_write_operations(self, client,
                                            authenticated_client, poll):
        """Test that write operations require authentication"""
        # Create poll
        create_data = {
            'question': 'New Poll',
            'options': ['Yes', 'No'],
            # 'start_date': current_time(),
            # 'expiry_date': one_hour_from_now()
        }

        response = client.post(reverse('poll-list'),
                               create_data, format='json')
        assert response.status_code in denied_status

        # Vote
        vote_data = {'option_index': 0}
        response = client.post(
            reverse('poll-vote', kwargs={'pk': poll.id}),
            vote_data,
            format='json'
        )
        assert response.status_code in denied_status

        # Both should work with authentication
        response = authenticated_client.post(
            reverse('poll-list'), create_data, format='json')
        print(f"authenticated vote response:{response.data}")
        assert response.status_code == status.HTTP_201_CREATED

        response = authenticated_client.post(
            reverse('poll-vote', kwargs={'pk': poll.id}),
            vote_data,
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
