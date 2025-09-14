# polls/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PollViewSet, VoteViewSet

router = DefaultRouter()
router.register(r'polls', PollViewSet)
router.register(r'my-votes', VoteViewSet, basename='myvote')

urlpatterns = [
    path('', include(router.urls)),
]
