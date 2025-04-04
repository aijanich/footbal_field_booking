from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FootballFieldViewSet, BookingViewSet

router = DefaultRouter()
router.register(r'fields', FootballFieldViewSet, basename='field')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]