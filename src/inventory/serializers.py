"""
Serializer for inventory
"""
from rest_framework import serializers
from .models import (Inventory, )

class InventorySerialier(serializers.ModelSerializer):
    """
    Inventory Serializer
    """
    class Meta:
        model = Inventory
        fields = ('__all__')
        
class LogoutInventorySerializer(serializers.ModelSerializer):
    """
    Logout serializer.
    """
    class Meta:
        model = Inventory
        fields = ('cf_strain_name', 'cf_cultivation_type', 'cf_potency', 'cf_cannabis_grade_and_category', 'available_stock', 'category_name')