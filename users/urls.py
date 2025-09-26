# users/urls.py
from django.urls import path
# from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/registration/', views.UserRegistrationView.as_view(),
         name='register'),
    path('auth/registration/verify-email/<str:token>/',
         views.verify_email, name='verify-email'),
    path('auth/registration/verify-email/',
         views.verify_email_request, name='verify-email-request'),
    path('auth/login/', views.user_login, name='login'),
    path('auth/logout/', views.user_logout, name='logout'),

    # Password management
    path('auth/password/change/',
         views.ChangePasswordView.as_view(), name='password-change'),
    path('auth/password/reset/', views.password_reset_request,
         name='password-reset-request'),
    path('auth/password/reset/confirm/',
         views.password_reset_confirm, name='password-reset-confirm'),

    # User profile
    path('auth/user/', views.UserProfileView.as_view(), name='user-detail'),

    # JWT tokens
    path('auth/token/verify/',
         views.CustomTokenVerifyView.as_view(), name='token-verify'),
    path('auth/token/refresh/',
         views.CustomTokenRefreshView.as_view(), name='token-refresh'),
]
