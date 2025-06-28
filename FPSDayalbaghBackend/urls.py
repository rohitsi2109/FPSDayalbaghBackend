from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import home_view

urlpatterns = [
    path('', home_view),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
]
# handler500 = server_error
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_ROOT, documents_root= settings.STATIC_ROOT)