from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User 
from .models import FootballField, Booking

@admin.register(FootballField)
class FootballFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'price_per_hour', 'is_active')
    list_filter = ('is_active', 'owner')
    search_fields = ('name', 'address')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'field', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'field', 'user')
    search_fields = ('user__username', 'field__name')
    
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'is_staff')
    list_filter = ('username', 'role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('username', 'email',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('phone_number',)}),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 
                      'is_superuser', 'groups', 
                      'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
