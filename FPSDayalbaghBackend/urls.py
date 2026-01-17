# project urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import home_view, CSRFTokenView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view),
    path('api/users/', include('users.urls')),
    path('api/', include('products.urls')),
    path("api/", include("orders.urls")),
    path('api/csrf/', CSRFTokenView.as_view(), name='csrf'),
    path("api/me/", include("notifications.urls")),
    path("api/", include("billing.urls")),
]

# ✅ Branding & Customization
admin.site.site_header = "FPS Admin"
admin.site.site_title = "FPS Admin Portal"
admin.site.index_title = "Welcome to FPS Admin Portal"

# Serve media/static only in dev
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
