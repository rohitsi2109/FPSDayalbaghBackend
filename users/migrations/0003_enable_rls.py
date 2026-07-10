from django.db import migrations


# Tables this project owns in the `public` schema. Enabling RLS without any
# policies blocks anon/authenticated/service_role access via Supabase's
# PostgREST API. Django connects as the table owner (the `postgres` role),
# which bypasses RLS by default (no FORCE ROW LEVEL SECURITY), so application
# behavior is unchanged.
TABLES = [
    # Project apps
    "public.users_user",
    "public.users_user_groups",
    "public.users_user_user_permissions",
    "public.products_category",
    "public.products_product",
    "public.orders_order",
    "public.orders_orderitem",
    "public.notifications_device",
    "public.billing_billinginvoice",
    "public.billing_billingitem",
    "public.billing_billingpayment",
    # Django built-ins
    "public.django_migrations",
    "public.django_content_type",
    "public.django_session",
    "public.django_admin_log",
    "public.auth_group",
    "public.auth_group_permissions",
    "public.auth_permission",
    # DRF authtoken
    "public.authtoken_token",
]

ENABLE_SQL = "\n".join(
    f"ALTER TABLE IF EXISTS {t} ENABLE ROW LEVEL SECURITY;" for t in TABLES
)
DISABLE_SQL = "\n".join(
    f"ALTER TABLE IF EXISTS {t} DISABLE ROW LEVEL SECURITY;" for t in TABLES
)


# Row Level Security is a PostgreSQL-only feature. Guard by vendor so this
# migration is a no-op on SQLite (used for local testing) while running the
# exact same SQL on Postgres/Supabase in production.
def _enable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(ENABLE_SQL)


def _disable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(DISABLE_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_alter_user_address_alter_user_phone"),
        ("products", "0004_alter_category_name_alter_product_name"),
        ("orders", "0005_add_created_at_index"),
        ("notifications", "0002_remove_device_is_active_and_more"),
        ("billing", "0002_billinginvoice_customer_name_and_more"),
    ]

    operations = [
        migrations.RunPython(_enable_rls, _disable_rls),
    ]
