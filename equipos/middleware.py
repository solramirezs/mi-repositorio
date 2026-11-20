# equipos/middleware.py

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Guardamos el usuario actual en un hilo local (thread local)
        # para que las señales de Django puedan acceder a él
        from .models import _thread_locals
        _thread_locals.user = request.user
        
        response = self.get_response(request)
        
        # Limpiamos al final de la petición
        _thread_locals.user = None
        return response