from django.contrib import admin
from .models import ShopItem, UserInventory


@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'price', 'is_default', 'is_active')
    list_filter = ('item_type', 'is_default', 'is_active')
    list_editable = ('price', 'is_default', 'is_active')
    search_fields = ('name',)
    fieldsets = (
        (None, {'fields': ('name', 'description', 'item_type', 'price', 'image')}),
        ('Тема', {'fields': ('css_class',), 'classes': ('collapse',)}),
        ('Доступность', {'fields': ('is_default', 'is_active')}),
    )


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'purchased_at')
    list_filter = ('item__item_type',)
    raw_id_fields = ('user',)
