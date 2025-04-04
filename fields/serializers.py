from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.gis.geos import Point
from .models import User, FootballField, Booking

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ['id', 'email', 'role', 'phone_number', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'read_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            phone_number=validated_data.get('phone_number', '')
        )
        return user

class FootballFieldSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    owner = UserSerializer(read_only=True)
    distance = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = FootballField
        fields = [
            'id', 'owner', 'name', 'address', 'contact_number',
            'price_per_hour', 'location', 'picture', 'facilities',
            'latitude', 'longitude', 'distance', 'is_available'
        ]
        read_only_fields = ['id', 'owner', 'location', 'distance', 'is_available']
        extra_kwargs = {
            'picture': {'required': False}
        }

    def get_distance(self, obj):
        request = self.context.get('request')
        if request and hasattr(obj, 'distance'):
            return obj.distance.m
        return None

    def get_is_available(self, obj):
        request = self.context.get('request')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        
        if start and end:
            return not obj.field_bookings.filter(
                start_time__lt=end,
                end_time__gt=start
            ).exists()
        return None

    def create(self, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['location'] = Point(longitude, latitude, srid=4326)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'latitude' in validated_data or 'longitude' in validated_data:
            longitude = validated_data.pop('longitude', instance.location.x)
            latitude = validated_data.pop('latitude', instance.location.y)
            instance.location = Point(longitude, latitude, srid=4326)
        return super().update(instance, validated_data)

class FieldDetailSerializer(FootballFieldSerializer):
    bookings = serializers.SerializerMethodField()
    rating = serializers.FloatField(source='average_rating', read_only=True)

    class Meta(FootballFieldSerializer.Meta):
        fields = FootballFieldSerializer.Meta.fields + [
            'description', 'bookings', 'rating', 'created_at'
        ]

    def get_bookings(self, obj):
        request = self.context.get('request')
        if request and request.user.role in ['admin', 'owner']:
            return BookingSerializer(obj.field_bookings.all(), many=True).data
        return None
    
class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    field_info = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'field', 'start_time', 'end_time',
            'status', 'created_at', 'field_info', 'user_email'
        ]
        read_only_fields = ['id', 'user',  'created_at', 'field_info', 'user_email']

    def get_field_info(self, obj):
        return {
            'name': obj.field.name,
            'price': obj.field.price_per_hour,
            'address': obj.field.address
        }

    def get_user_email(self, obj):
        return obj.user.email

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")

        if self.instance:  # Update operation
            overlapping = Booking.objects.filter(
                field=data.get('field', self.instance.field),
                start_time__lt=data.get('end_time', self.instance.end_time),
                end_time__gt=data.get('start_time', self.instance.start_time)
            ).exclude(id=self.instance.id).exists()
        else:  # Create operation
            overlapping = Booking.objects.filter(
                field=data['field'],
                start_time__lt=data['end_time'],
                end_time__gt=data['start_time']
            ).exists()

        if overlapping:
            raise serializers.ValidationError("This time slot is already booked")

        # Prevent users from booking their own fields
        if self.context['request'].user == data['field'].owner:
            raise serializers.ValidationError("Cannot book your own field")

        return data

