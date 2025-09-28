# users/schema.py
from drf_yasg import openapi
# from drf_yasg.utils import swagger_auto_schema
# from rest_framework import status

# Common parameter definitions
email_parameter = openapi.Parameter(
    'email',
    openapi.IN_FORM,
    description="User's email address",
    type=openapi.TYPE_STRING,
    format=openapi.FORMAT_EMAIL
)

# token_parameter = openapi.Parameter(
#    'token',
#    openapi.IN_PATH,
#    description="Verification token from email",
#    type=openapi.TYPE_STRING
# )

# Common response schemas
user_profile_response = openapi.Response(
    description="User profile data",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_STRING,
                                 format=openapi.FORMAT_UUID),
            'email': openapi.Schema(type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_EMAIL),
            # 'email_verified': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'date_joined': openapi.Schema(type=openapi.TYPE_STRING,
                                          format=openapi.FORMAT_DATETIME),
        }
    )
)

auth_token_response = openapi.Response(
    description="JWT tokens with user data",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'access': openapi.Schema(type=openapi.TYPE_STRING,
                                     description='JWT access token'),
            'refresh': openapi.Schema(type=openapi.TYPE_STRING,
                                      description='JWT refresh token'),
            'user': openapi.Schema(type=openapi.TYPE_OBJECT,
                                   description='User profile data'),
        }
    )
)

error_response = openapi.Response(
    description="Validation errors",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING),
            'code': openapi.Schema(type=openapi.TYPE_STRING),
        }
    )
)

# Request body schemas
registration_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'password', 'password_confirm'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_EMAIL),
        'password': openapi.Schema(type=openapi.TYPE_STRING,
                                   minLength=8, maxLength=128),
        'password_confirm': openapi.Schema(type=openapi.TYPE_STRING,
                                           minLength=8, maxLength=128),
    }
)

login_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'password'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_EMAIL),
        'password': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

password_change_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['current_password', 'new_password', 'new_password_confirm'],
    properties={
        'current_password': openapi.Schema(type=openapi.TYPE_STRING),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING,
                                       minLength=8, maxLength=128),
        'new_password_confirm': openapi.Schema(type=openapi.TYPE_STRING,
                                               minLength=8, maxLength=128),
    }
)

password_reset_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_EMAIL),
    }
)

password_reset_confirm_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['token', 'new_password', 'new_password_confirm'],
    properties={
        'token': openapi.Schema(type=openapi.TYPE_STRING),
        'new_password': openapi.Schema(type=openapi.TYPE_STRING,
                                       minLength=8, maxLength=128),
        'new_password_confirm': openapi.Schema(type=openapi.TYPE_STRING,
                                               minLength=8, maxLength=128),
    }
)

# email_verification_request_body = openapi.Schema(
#    type=openapi.TYPE_OBJECT,
#    required=['email'],
#    properties={
#        'email': openapi.Schema(type=openapi.TYPE_STRING,
#                                format=openapi.FORMAT_EMAIL),
#    }
# )

token_verify_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['token'],
    properties={
        'token': openapi.Schema(type=openapi.TYPE_STRING),
    }
)

token_refresh_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['refresh'],
    properties={
        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
    }
)
