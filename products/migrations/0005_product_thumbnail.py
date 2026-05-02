from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_alter_category_name_alter_product_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="thumbnail",
            field=models.ImageField(blank=True, null=True, upload_to="products/thumbs/"),
        ),
    ]
