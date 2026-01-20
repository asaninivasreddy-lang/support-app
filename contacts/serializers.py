from rest_framework import serializers
from .models import GlobalContacts


class GlobalContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalContacts
        fields = ['id', 'name', 'phone_number', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']      

