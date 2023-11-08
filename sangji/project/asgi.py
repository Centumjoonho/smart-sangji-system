import os

import django
from channels.auth import AuthMiddlewareStack
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
import app_socket.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

application = ProtocolTypeRouter({
    'http' : AsgiHandler(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            app_socket.routing.websocket_urlpatterns
        )
    ),
})