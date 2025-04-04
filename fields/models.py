from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.gis.db import models as gis_models  # For GeoDjango integration
from django.core.validators import MinValueValidator
from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(username, password, **extra_fields)

class User(AbstractUser):
    """
    Custom user model with role-based access control
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('owner', 'Field Owner'),
        ('user', 'Regular User'),
    )
    
    username = models.CharField(
        max_length=150,  # Maximum length of the username
        unique=True,  # Ensure usernames are unique
        blank=False,  # Make the username field mandatory
        null=False,  # The field cannot be null
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
   
    USERNAME_FIELD = 'username'

    # Assign the custom manager
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"

class FootballField(gis_models.Model):
    """
    Football field model with geolocation support
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='managed_fields',
        limit_choices_to={'role': 'owner'}
    )
    name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    price_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    location = gis_models.PointField(srid=4326)  # WGS84 coordinate system
    picture = models.ImageField(
        upload_to='field_pictures/',
        null=True,
        blank=True
    )
    facilities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Available facilities (e.g., {'showers': True, 'parking': False})"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.address}"

class Booking(models.Model):
    """
    Booking system model with time slot management
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_bookings'
    )
    field = models.ForeignKey(
        FootballField,
        on_delete=models.CASCADE,
        related_name='field_bookings'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('cancelled', 'Cancelled')
        ),
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['field', 'start_time', 'end_time'],
                name='unique_booking_slot'
            ),
            models.CheckConstraint(
                check=models.Q(end_time__gt=models.F('start_time')),
                name='end_time_after_start_time'
            )
        ]
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.field.name} ({self.start_time} to {self.end_time})"