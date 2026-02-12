from rest_framework.throttling import SimpleRateThrottle

class RegisterThrottle(SimpleRateThrottle):
    scope = 'register'
    
    def get_cache_key(self, request, view):
        email = request.data.get('email')
        if email:
            return self.cache_format % {
                'scope': self.scope,
                'ident': email
            }
        return request.META.get('REMOTE_ADDR')

class BasketThrottle(SimpleRateThrottle):
    scope = 'basket'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk
            }
        return None