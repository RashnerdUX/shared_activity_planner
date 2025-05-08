from django.core.cache import cache
from rest_framework import serializers

from api.models import Location


class LocationSerializer(serializers.ModelSerializer):
    map_data = serializers.SerializerMethodField()
    
    def get_map_data(self, obj):
        """
        Format data for map display
        """
        if obj.latitude and obj.longitude:
            return {
                'position': {
                    'lat': obj.latitude,
                    'lng': obj.longitude
                },
                'title': obj.name,
                'address': obj.address,
                'content': f"{obj.name}, {obj.city}"
            }
        return None

    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'city', 'country', 'latitude', 'longitude', 'details', 'map_data']
        read_only_fields = ['latitude', 'longitude']

    def create(self, validated_data):
        address = validated_data.get("address")
        location = Location.objects.create(**validated_data)

        if address:
            from api.tasks import standardize_location
            standardize_location.delay(address=location.address, location_id=location.pk)
        return location
    
    def update(self, instance, validated_data):
        address = validated_data.get("address")

        if address:
            from api.tasks import standardize_location
            standardize_location.delay(address=address, location_id=instance.pk)
        return super().update(instance, validated_data)
