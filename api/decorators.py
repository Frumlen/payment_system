from functools import wraps
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from django.utils.decorators import available_attrs
from django.core.exceptions import ValidationError

#TODO: Implement as middleware
def handle_error_json():
    """
    Decorator for JSON views
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except ValidationError as err:
                return Response(err.message, status=HTTP_400_BAD_REQUEST)
            except serializers.ValidationError as err:
                return Response(err.detail, status=HTTP_400_BAD_REQUEST)
            except Exception as err:
                return Response(data={'non_field_errors': ["{}".format(err)]}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        return _wrapped_view
    return decorator
