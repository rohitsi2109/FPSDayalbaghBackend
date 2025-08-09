from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'thumb')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')
    readonly_fields = ('preview',)
    fields = ('name', 'category', 'price', 'stock', 'image', 'preview')

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.image.url)
        return '-'
    thumb.short_description = 'Image'

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-height:220px;border:1px solid #e5e7eb;padding:6px;border-radius:8px;" />',
                obj.image.url
            )
        return 'Upload an image and save to see a preview.'
    preview.short_description = 'Preview'
