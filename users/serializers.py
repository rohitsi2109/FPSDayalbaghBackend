# # from rest_framework import serializers
# # from .models import User
# #
# # class RegisterSerializer(serializers.ModelSerializer):
# #     confirm_phone = serializers.CharField(write_only=True)
# #     confirm_password = serializers.CharField(write_only=True)
# #     password = serializers.CharField(write_only=True, min_length=6)
# #
# #     class Meta:
# #         model = User
# #         fields = ['name', 'phone', 'confirm_phone', 'password', 'confirm_password', 'address', 'gender']
# #         extra_kwargs = {
# #             'gender': {'required': False},
# #         }
# #
# #     def validate(self, data):
# #         if data['phone'] != data['confirm_phone']:
# #             raise serializers.ValidationError("Phone numbers do not match.")
# #         if data['password'] != data['confirm_password']:
# #             raise serializers.ValidationError("Passwords do not match.")
# #         return data
# #
# #     def create(self, validated_data):
# #         validated_data.pop('confirm_phone')
# #         validated_data.pop('confirm_password')
# #         password = validated_data.pop('password')
# #         user = User.objects.create_user(password=password, **validated_data)
# #         return user
# #
# #
# # class LoginSerializer(serializers.Serializer):
# #     phone = serializers.CharField()
# #     password = serializers.CharField()
#
#
# from rest_framework import serializers
# from .models import User
#
# # Use this to return user details with the token
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             "id",
#             "name",
#             "phone",
#             "address",
#             "gender",
#             "is_active",
#             "date_joined",
#             "last_login",
#         )
#         read_only_fields = fields
#
#
# class RegisterSerializer(serializers.ModelSerializer):
#     confirm_phone = serializers.CharField(write_only=True)
#     confirm_password = serializers.CharField(write_only=True)
#     password = serializers.CharField(write_only=True, min_length=6, style={"input_type": "password"})
#
#     class Meta:
#         model = User
#         fields = ["name", "phone", "confirm_phone", "password", "confirm_password", "address", "gender"]
#         extra_kwargs = {"gender": {"required": False}}
#
#     def validate(self, data):
#         if data["phone"] != data["confirm_phone"]:
#             raise serializers.ValidationError({"confirm_phone": "Phone numbers do not match."})
#         if data["password"] != data["confirm_password"]:
#             raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
#         if User.objects.filter(phone=data["phone"]).exists():
#             raise serializers.ValidationError({"phone": "A user with this phone already exists."})
#         return data
#
#     def create(self, validated_data):
#         validated_data.pop("confirm_phone", None)
#         validated_data.pop("confirm_password", None)
#         password = validated_data.pop("password")
#         user = User.objects.create_user(password=password, **validated_data)
#         return user
#
#
# class LoginSerializer(serializers.Serializer):
#     phone = serializers.CharField()
#     password = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})
#




from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    # Declare these explicitly so DRF doesn't expect model fields
    is_active = serializers.SerializerMethodField()
    date_joined = serializers.SerializerMethodField()
    last_login = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "name",
            "phone",
            "address",
            "gender",
            "is_active",
            "date_joined",
            "last_login",
        )

    def get_is_active(self, obj):
        # Fallback True if field not present on model
        return getattr(obj, "is_active", True)

    def get_date_joined(self, obj):
        # Return None if absent; DRF will render as null
        return getattr(obj, "date_joined", None)

    def get_last_login(self, obj):
        return getattr(obj, "last_login", None)


class RegisterSerializer(serializers.ModelSerializer):
    confirm_phone = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=6, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["name", "phone", "confirm_phone", "password", "confirm_password", "address", "gender"]
        extra_kwargs = {"gender": {"required": False}}

    def validate(self, data):
        if data["phone"] != data["confirm_phone"]:
            raise serializers.ValidationError({"confirm_phone": "Phone numbers do not match."})
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        if User.objects.filter(phone=data["phone"]).exists():
            raise serializers.ValidationError({"phone": "A user with this phone already exists."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_phone", None)
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})
