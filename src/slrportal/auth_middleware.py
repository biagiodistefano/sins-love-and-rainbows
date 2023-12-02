from django.contrib.auth import login
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

from .auth_backend import CustomQueryParamAuthentication


class CustomQueryParamMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest) -> None:
        if request.user.is_authenticated:
            return
        if visitor_id := request.GET.get('visitor_id'):
            backend = CustomQueryParamAuthentication()
            if user := backend.authenticate(request, visitor_id=visitor_id):
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                request.user = user
                login(request, user)
