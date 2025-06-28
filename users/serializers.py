from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    confirm_phone = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['name', 'phone', 'confirm_phone', 'password', 'confirm_password', 'address', 'gender']
        extra_kwargs = {
            'gender': {'required': False},
        }

    def validate(self, data):
        if data['phone'] != data['confirm_phone']:
            raise serializers.ValidationError("Phone numbers do not match.")
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_phone')
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()
