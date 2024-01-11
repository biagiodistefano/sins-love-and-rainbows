from threading import local

_user_host_thread_local = local()


def get_current_host():
    return getattr(_user_host_thread_local, 'host', None)


class HostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user_host_thread_local.host = request.get_host()
        response = self.get_response(request)
        return response
