from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def root_view(request):
    """Simple root view to confirm API is running"""
    return JsonResponse({
        'message': 'INTELLIQ SHC API is running',
        'status': 'ok',
        'version': '1.0',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/',
            'login': '/api/login/',
            'register': '/api/register/',
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

