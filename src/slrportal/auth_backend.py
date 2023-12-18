from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core import exceptions
from django.http import HttpRequest

User = get_user_model()


class CustomQueryParamAuthentication(ModelBackend):
    def authenticate(self, request: HttpRequest, visitor_id: str = None, **kwargs) -> User | None:
        if visitor_id:
            try:
                user = User.objects.get(id=visitor_id, is_staff=False, is_admin=False)
                return user
            except (User.DoesNotExist, exceptions.ValidationError):
                pass
        return None

    def get_user(self, user_id: str) -> User | None:
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
