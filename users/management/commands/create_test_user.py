from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Creates a test user for Google Play closed testing'

    def handle(self, *args, **kwargs):
        phone = '9999999999'
        password = 'TestFPS@123'
        name = 'Test User'
        address = 'Dayalbagh, Agra, Uttar Pradesh - 282005'

        if User.objects.filter(phone=phone).exists():
            self.stdout.write(self.style.WARNING(f'Test user already exists (phone: {phone})'))
            return

        User.objects.create_user(
            phone=phone,
            name=name,
            address=address,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS('Test user created successfully'))
        self.stdout.write(f'  Phone    : {phone}')
        self.stdout.write(f'  Password : {password}')
