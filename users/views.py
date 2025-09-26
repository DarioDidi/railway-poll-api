# users/views.py
from .utils import (send_verification_email, send_password_reset_email,
                    verify_email_token, verify_password_reset_token)
from .serializers import *
from .models import User
from django.utils import timezone
from django.contrib.auth import login, logout
from rest_framework_simplejwt.views import TokenVerifyView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, generics, permissions
from django.http import JsonResponse
from django.views import View
# from allauth.account.models import (EmailConfirmation,
#                                    get_emailconfirmation_model)
# from allauth.account.internal.flows.email_verification\
#    import verify_email
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .schema import *

import logging

logger = logging.getLogger(__name__)


class APIConfirmEmailView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        key = kwargs.get('key')
        print(f"in get key:{key}")

        if not key:
            return JsonResponse({'error': 'Missing confirmation key'},
                                status=400)

        print("trying")
        try:
            model = get_emailconfirmation_model()
            emailconfirmation = model.from_key(key)
            if emailconfirmation is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid confirmation key'
                }, status=400)

            # Verify the email address
            success = verify_email(request, emailconfirmation.email_address)
            print(f"EMail verified?{success}")

            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Email verified successfully',
                    'email': emailconfirmation.email_address.email
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Email verification failed'
                }, status=400)

        except EmailConfirmation.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid confirmation key'
            }, status=400)
        except Exception as e:
            logger.error(f"Email confirmation error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Internal server error'
            }, status=500)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Register new user",
        operation_description=("Creates a new user account"
                               "and sends email verification."
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
                        'detail': ('User registered successfully.'
                                   'Please check your email for verification.'),
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
        send_verification_email(user, request)

        return Response(
            {
                "detail": ("User registered successfully."
                           " Please check your email for verification."),
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
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, maxLength=50),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, maxLength=50),
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
        operation_description="Change authenticated user's password. Requires current password for verification.",
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

        return Response({"detail": "Password updated successfully."})


@swagger_auto_schema(
    method='post',
    operation_summary="Request password reset",
    operation_description=("Request password reset email."
                           " Always returns success to prevent email enumeration."),
    request_body=password_reset_request_body,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Reset email sent if account exists",
            examples={
                'application/json': {
                    'detail': ('If the email exists,'
                               ' a password reset link has been sent.')
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
    try:
        user = User.objects.get(email__iexact=email)
        if user.is_active:
            send_password_reset_email(user, request)
    except User.DoesNotExist:
        pass  # Don't reveal whether email exists

    return Response({
        "detail": "If the email exists, a password reset link has been sent."
    })


@swagger_auto_schema(
    method='post',
    operation_summary="Confirm password reset",
    operation_description=("Confirm password reset using"
                           " token from email. Token expires in 1 hour."),
    request_body=password_reset_confirm_body,
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
            description="Invalid or expired token",
            examples={
                'application/json': {
                    'detail': 'Invalid or expired token.'
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

    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    user = verify_password_reset_token(token)
    if not user:
        return Response(
            {"detail": "Invalid or expired token."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()

    # Mark token as used
    from .models import PasswordResetToken
    PasswordResetToken.objects.filter(token=token).update(used=True)

    return Response({"detail": "Password reset successfully."})


@swagger_auto_schema(
    method='get',
    operation_summary="Verify email address",
    operation_description=("Verify email address using token from"
                           " verification email"
                           " (GET endpoint for email links)."),
    manual_parameters=[token_parameter],
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Email verified successfully",
            examples={
                'application/json': {
                    'detail': 'Email verified successfully.'
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Invalid or expired token",
            examples={
                'application/json': {
                    'detail': 'Invalid or expired verification token.'
                }
            }
        )
    },
    tags=['verification']
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request, token):
    """GET endpoint for email verification (clicking link in email)"""
    user = verify_email_token(token)

    if not user:
        return Response(
            {"detail": "Invalid or expired verification token."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.email_verified = True
    user.save()

    # Mark token as used
    from .models import EmailVerificationToken
    EmailVerificationToken.objects.filter(token=token).update(used=True)

    return Response({"detail": "Email verified successfully."})


@swagger_auto_schema(
    method='post',
    operation_summary="Request email verification",
    operation_description=("Request new email verification email"
                           " to be sent. Rate limited to prevent spam."),
    request_body=email_verification_request_body,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="Verification email sent",
            examples={
                'application/json': {
                    'detail': 'Verification email sent.'
                }
            }
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Email already verified or not found",
            examples={
                'application/json': {
                    'detail': 'Email is already verified.'
                }
            }
        ),
        status.HTTP_429_TOO_MANY_REQUESTS: openapi.Response(
            description="Too many requests",
            examples={
                'application/json': {
                    'detail': 'Please wait before requesting another verification email.'
                }
            }
        )
    },
    tags=['verification']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email_request(request):
    """Request a new verification email"""
    serializer = EmailVerificationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    try:
        user = User.objects.get(email__iexact=email)
        if user.email_verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent email spam
        if (user.last_email_sent and
                (timezone.now() - user.last_email_sent).seconds < 300):  # 5 minutes
            return Response(
                {"detail": "Please wait before requesting another verification email."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        send_verification_email(user, request)
        return Response({"detail": "Verification email sent."})

    except User.DoesNotExist:
        return Response(
            {"detail": "User with this email does not exist."},
            status=status.HTTP_404_NOT_FOUND
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
