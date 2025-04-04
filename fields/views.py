from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from django.utils import timezone
from .models import FootballField, Booking, User
from .serializers import (
    FootballFieldSerializer,
    BookingSerializer,
    FieldDetailSerializer
)
from .permissions import IsOwnerOrReadOnly, IsFieldOwner, CanDeleteFootballField

class FootballFieldViewSet(viewsets.ModelViewSet):
    """
    Viewset for football field operations
    - List/show fields with filtering/sorting
    - CRUD operations for field owners
    - Admin has full access
    """
    queryset = FootballField.objects.all()
    serializer_class = FootballFieldSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """Use different serializer for detailed view"""
        if self.action == 'retrieve':
            return FieldDetailSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'destroy':
            return [CanDeleteFootballField()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Additional safety check
        future_bookings = instance.field_bookings.filter(
            end_time__gt=timezone.now()
        )
        
        if future_bookings.exists():
            return Response(
                {
                    "detail": "Field has upcoming bookings that must be canceled first",
                    "bookings": BookingSerializer(future_bookings, many=True).data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

       
    # def get_queryset(self):
    #     """
    #     Enhanced queryset with:
    #     - Availability filtering by date range
    #     - Location-based sorting
    #     - Owner-based filtering for owners
    #     """
    #     queryset = super().get_queryset()
    #     params = self.request.query_params

    #     # Availability filtering
    #     start = params.get('start')
    #     end = params.get('end')
    #     if start and end:
    #         start_time = parse_datetime(start)
    #         end_time = parse_datetime(end)
            
    #         # Find conflicting bookings
    #         conflicting_bookings = Booking.objects.filter(
    #             Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
    #         ).values_list('field_id', flat=True)
            
    #         queryset = queryset.exclude(id__in=conflicting_bookings)

    #     # Location-based sorting
    #     lat = params.get('lat')
    #     lng = params.get('lng')
    #     if lat and lng:
    #         try:
    #             user_location = Point(float(lng), float(lat), srid=4326)
    #             queryset = queryset.annotate(
    #                 distance=Distance('location', user_location)
    #             ).order_by('distance')
    #         except ValueError:
    #             pass

    #     # Owner-based filtering
    #     if self.request.user.is_authenticated and self.request.user.role == 'owner':
    #         queryset = queryset.filter(owner=self.request.user)

    #     return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        lat = params.get('lat')
        lng = params.get('lng')
        print(f"Received lat: {lat}, lng: {lng}")  # Debugging: Check if values are being passed

        if lat and lng:
            try:
                user_location = Point(float(lng), float(lat), srid=4326)
                queryset = queryset.annotate(
                    distance=Distance('location', user_location)
                ).order_by('distance')  # Sorting by calculated distance
                
                # Print distances for debugging
                for field in queryset:
                    print(f"Field: {field.name}, Distance: {field.distance.m} meters")

            except ValueError:
                print("Invalid coordinates provided")

        return queryset

    @action(detail=True, methods=['get'])
    def bookings(self, request, pk=None):
        """Get bookings for a specific field"""
        field = self.get_object()
        bookings = field.field_bookings.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Auto-set owner when creating field"""
        serializer.save(owner=self.request.user)

class BookingViewSet(viewsets.ModelViewSet):
    """
    Viewset for booking operations
    - Users can create/view their bookings
    - Field owners can manage bookings for their fields
    - Admins have full access
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Custom queryset based on user role"""
        user = self.request.user
        
        if user.role == 'admin':
            return Booking.objects.all()
        
        if user.role == 'owner':
            return Booking.objects.filter(field__owner=user)
        
        return Booking.objects.filter(user=user)

    def get_permissions(self):
        """Additional permissions for delete/update"""
        if self.action in ['destroy', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsFieldOwner()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Handle booking creation with conflict check"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Manual validation for booking conflicts
        field = serializer.validated_data['field']
        start = serializer.validated_data['start_time']
        end = serializer.validated_data['end_time']
        
        if Booking.objects.filter(
            field=field,
            start_time__lt=end,
            end_time__gt=start
        ).exists():
            return Response(
                {'error': 'Time slot already booked'},
                status=status.HTTP_409_CONFLICT
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        """Auto-set user when creating booking"""
        serializer.save(user=self.request.user)