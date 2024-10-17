import requests
from django.contrib.auth.backends import BaseBackend
from .models import User
from requests.auth import HTTPBasicAuth
from django.contrib.auth.hashers import check_password
from django.contrib import messages 
from django.db.models import Q


class ApiBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            if username in ['admin', 'admin@admin.com']:
                if check_password(password, user.password):
                    return user
                else:
                    messages.error(request, "LOGIN : Mot de passe incorrect.")
                    return None
            
            auth = HTTPBasicAuth(user.email, password)

            response = requests.post('https://api.ldap.groupe-hasnaoui.com/pumaprd/auth', auth=auth)

            if not response.status_code == 200:
                messages.error(request, "LOGIN : Problème avec la connexion au serveur.")
            else:
                if not response.json().get('authenticated'):
                    messages.error(request, "LOGIN : Mot de passe incorrect.")
                else:
                    return user
        except User.DoesNotExist:
            messages.error(request, "LOGIN : Utilisateur pas trouvé.")
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
