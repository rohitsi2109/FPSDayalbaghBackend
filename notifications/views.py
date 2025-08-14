from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Device

class RegisterDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        platform = request.data.get('platform', 'android').lower()
        if not token:
            return Response({'error': 'token required'}, status=status.HTTP_400_BAD_REQUEST)

        device, _ = Device.objects.update_or_create(
            token=token,
            defaults={'user': request.user, 'platform': platform, 'is_active': True},
        )
        return Response({'ok': True, 'device_id': device.id})

class UnregisterDeviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'token required'}, status=status.HTTP_400_BAD_REQUEST)
        Device.objects.filter(token=token, user=request.user).update(is_active=False)
        return Response({'ok': True})
