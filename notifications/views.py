# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Device
from .serializers import DeviceSerializer
from .fcm import send_to_tokens

class DeviceRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = DeviceSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data["token"]
        defaults = {
            "platform": ser.validated_data.get("platform", "android"),
            "is_admin": ser.validated_data.get("is_admin", False),
            "user": request.user,
        }
        d, created = Device.objects.update_or_create(token=token, defaults=defaults)
        return Response(
            {"ok": True, "created": created, "platform": d.platform, "is_admin": d.is_admin}
        )

class DeviceDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "token required"}, status=status.HTTP_400_BAD_REQUEST)
        Device.objects.filter(token=token, user=request.user).delete()
        return Response({"ok": True})

class DeviceTestPushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # If token provided in body, use it; else send to all of current user's tokens
        token = request.data.get("token")
        tokens = [token] if token else list(
            Device.objects.filter(user=request.user).values_list("token", flat=True)
        )
        result = send_to_tokens(tokens, "Test push", "It works 🎉", data={"order_id": "0"})
        return Response(result)
