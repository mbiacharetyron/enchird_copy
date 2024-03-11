from django.utils import timezone
from knox.models import AuthToken
from knox.settings import CONSTANTS
from knox.auth import TokenAuthentication
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser




class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            # Get the query string parameters from the scope
            query_string = scope.get("query_string", b"").decode("utf-8")

            # Parse the query string to get the token
            token_param = next((param.split("=") for param in query_string.split("&") if param.startswith("token=")), None)

            if token_param: 
                token_key = token_param[1]
                
                scope["user"] = await self.get_user_from_token(token_key)
                
            return await super().__call__(scope, receive, send)
        except AuthToken.DoesNotExist:
            raise ValueError("Invalid token or Knox object not found")
        except Exception as e:
            raise ValueError(f"Error processing token: {str(e)}")
            

    @database_sync_to_async
    def get_user_from_token(self, key):
        try:
            knox_object = AuthToken.objects.filter(token_key=key[:CONSTANTS.TOKEN_KEY_LENGTH]).first()
            if knox_object and knox_object.expiry:
                current_time = timezone.now()

                # Compare the expiry timestamp with the current time
                if knox_object.expiry < current_time:
                    # The token is not expired
                    return None  # or raise an exception
                else:
                    return knox_object.user
                    
            else:
                # The Knox object is not found (invalid token)
                return None  # or raise an exception
        
        except AuthToken.DoesNotExist:
            return AnonymousUser()
        
        
        
        
        
        