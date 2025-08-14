# notifications/urls.py
from django.urls import path
from .views import DeviceRegisterView, DeviceDeleteView, DeviceTestPushView

urlpatterns = [
    path("devices/", DeviceRegisterView.as_view(), name="device-register"),
    path("devices/delete/", DeviceDeleteView.as_view(), name="device-delete"),
    path("devices/test/", DeviceTestPushView.as_view(), name="device-test"),
]
