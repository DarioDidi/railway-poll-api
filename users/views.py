# users/views.py
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
