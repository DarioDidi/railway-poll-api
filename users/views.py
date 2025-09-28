# users/views.py
from .utils import (generate_reset_code, store_reset_code,
                    verify_reset_code, clear_reset_code)
from .serializers import (UserRegistrationSerializer, UserLoginSerializer,
                          UserProfileSerializer, ChangePasswordSerializer,
                          PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer)
from .models import User
from django.contrib.auth import login, logout
from rest_framework_simplejwt.views import TokenVerifyView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, generics, permissions

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .schema import (
    registration_request_body, password_change_request_body,
    error_response, login_request_body, auth_token_response,
    user_profile_response, token_verify_body,
    token_refresh_body)

import logging

logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register new user",
        operation_description=("Creates a new user account"
                               "Username is auto-generated from email."),
        request_body=registration_request_body,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING),
                        'user_id': openapi.Schema(type=openapi.TYPE_STRING,
                                                  format=openapi.FORMAT_UUID),
                    }
                ),
                examples={
                    'application/json': {
                        'detail': 'User registered successfully.',
                        'user_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
                    }
                }
            ),
            status.HTTP_400_BAD_REQUEST: error_response
        },
        tags=['authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        # send_verification_email(user, request)

        return Response(
            {
                "detail": ("User registered successfully."),
                "user_id": str(user.id)
            },
            status=status.HTTP_201_CREATED
        )


@swagger_auto_schema(
    method='post',
    operation_summary="User login",
    operation_description=("Authenticate user with email "
                           "and password. Returns JWT tokens and user data."),
    request_body=login_request_body,
    responses={
        status.HTTP_200_OK: auth_token_response,
        status.HTTP_400_BAD_REQUEST: error_response
    },
    tags=['authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login(request):
    serializer = UserLoginSerializer(
        data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']
    login(request, user)

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    user_data = UserProfileSerializer(user).data

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': user_data
    })


@swagger_auto_schema(
    method='post',
    operation_summary="User logout",
    operation_description="Logout authenticated user and invalidate session.",
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Logout successful",
            examples={
                'application/json': {
                    'detail': 'Successfully logged out.'
                }
            }
        ),
        status.HTTP_401_UNAUTHORIZED: error_response
    },
    tags=['authentication']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def user_logout(request):
    logout(request)
    return Response({"detail": "Successfully logged out."})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description=("Retrieve authenticated"
                               " user's profile information."),
        responses={
            status.HTTP_200_OK: user_profile_response,
            status.HTTP_401_UNAUTHORIZED: error_response
        },
        tags=['profile']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description=("Update authenticated user's"
                               " profile information."
                               " Email cannot be changed."),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING,
                                             maxLength=50),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING,
                                            maxLength=50),
            }
        ),
        responses={
            status.HTTP_200_OK: user_profile_response,
            status.HTTP_400_BAD_REQUEST: error_response,
            status.HTTP_401_UNAUTHORIZED: error_response
        },
        tags=['profile']
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partial update user profile",
        operation_description=("Partially update authenticated"
                               " user's profile information."),
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING,
                                             maxLength=50),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING,
                                            maxLength=50),
            }
        ),
        responses={
            status.HTTP_200_OK: user_profile_response,
            status.HTTP_400_BAD_REQUEST: error_response,
            status.HTTP_401_UNAUTHORIZED: error_response
        },
        tags=['profile']
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_summary="Change password",
        operation_description=("Change authenticated user's password."
                               " Requires current password for verification."),
        request_body=password_change_request_body,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Password changed successfully",
                examples={
                    'application/json': {
                        'detail': 'Password updated successfully.'
                    }
                }
            ),
            status.HTTP_400_BAD_REQUEST: error_response,
            status.HTTP_401_UNAUTHORIZED: error_response
        },
        tags=['password']
    )
    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Update session if using session authentication
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        # Logout user from current session
        logout(request)
        response_data = {
            "detail": ("Password updated successfully."
                       " Please login again with your new password."),
            "logout_required": True
        }

        return Response(response_data)


@swagger_auto_schema(
    method='post',
    operation_summary="Request password reset code",
    operation_description=(
        "Generate a password reset code for the user."
        " Returns the code directly."),
    request_body=PasswordResetRequestSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Reset code generated",
            examples={
                'application/json': {
                    'reset_code': '123456',
                    'email': 'user@example.com',
                    'expires_in': 900
                }
            }
        )
    },
    tags=['password']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    reset_code = generate_reset_code()
    store_reset_code(email, reset_code)

    return Response({
        "reset_code": reset_code,
        "email": email,
        "expires_in": 900,  # 15 minutes in seconds
        "detail": ("Use this code to reset your password."
                   " Code expires in 15 minutes.")
    })


@swagger_auto_schema(
    method='post',
    operation_summary="Confirm password reset with code",
    operation_description=(
        "Reset password using the code received from the reset request."),
    request_body=PasswordResetConfirmSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Password reset successful",
            examples={
                'application/json': {
                    'detail': 'Password reset successfully.'
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Invalid code or validation error",
            examples={
                'application/json': {
                    'detail': 'Invalid or expired reset code.'
                }
            }
        )
    },
    tags=['password']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    reset_code = serializer.validated_data['reset_code']
    new_password = serializer.validated_data['new_password']

    # Verify reset code
    if not verify_reset_code(email, reset_code):
        return Response(
            {"detail": "Invalid or expired reset code."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email__iexact=email)
        user.set_password(new_password)
        user.save()
        clear_reset_code(email)

        return Response({"detail": "Password reset successfully."})

    except User.DoesNotExist:
        return Response(
            {"detail": "User not found."},
            status=status.HTTP_400_BAD_REQUEST
        )
# JWT Token Views (using simplejwt)


class CustomTokenVerifyView(TokenVerifyView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Verify JWT token",
        operation_description="Verify validity of JWT access token.",
        request_body=token_verify_body,
        responses={
            status.HTTP_200_OK: openapi.Response(description="Token is valid"),
            status.HTTP_401_UNAUTHORIZED: error_response
        },
        tags=['tokens']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Refresh JWT token",
        operation_description="Refresh JWT access token using refresh token.",
        request_body=token_refresh_body,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    'application/json': {
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                    }
                }
            ),
            status.HTTP_401_UNAUTHORIZED: error_response
        },
        tags=['tokens']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
