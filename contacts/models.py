from django.core.validators import RegexValidator
from django.db import models

class GlobalContacts(models.Model):
    name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(
        max_length=16,  
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{6,14}$',
                message="Enter a valid phone number (7-15 digits, optional +)."
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"
