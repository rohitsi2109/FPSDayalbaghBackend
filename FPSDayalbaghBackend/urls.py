from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import home_view, CSRFTokenView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view),
    path('api/users/', include('users.urls')),
    path('api/csrf/', CSRFTokenView.as_view(), name='csrf')
]
# handler500 = server_error
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_ROOT, documents_root= settings.STATIC_ROOT)