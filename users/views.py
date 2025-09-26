# users/views.py
from .utils import send_verification_email, send_password_reset_email, verify_email_token, verify_password_reset_token
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
from allauth.account.models import (EmailConfirmation,
                                    get_emailconfirmation_model)
from allauth.account.internal.flows.email_verification\
    import verify_email
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        send_verification_email(user, request)

        return Response(
            {
                "detail": "User registered successfully. Please check your email for verification.",
                "user_id": str(user.id)
            },
            status=status.HTTP_201_CREATED
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


@api_view(['POST'])
def user_logout(request):
    logout(request)
    return Response({"detail": "Successfully logged out."})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Update session if using session authentication
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        return Response({"detail": "Password updated successfully."})


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


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
