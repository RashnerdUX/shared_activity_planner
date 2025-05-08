import googlemaps
import dotenv
import os
import json
import hashlib

from django.db import models
from django.core.cache import cache

dotenv.load_dotenv()
class Location(models.Model):
    """
    This is the model that helps the users set a location for an event. It will be vsiible to everyone and tell them exactly where to go for the event
    """
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=1000, blank=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} can be found at {self.address}"
    
    def geocode_address(self, address):
        """
        This method gets the longitude and latitude for a location
        """
        try:    
            maps = googlemaps.Client(key=os.getenv("GOOGLE_MAP_KEY"))
            geocode_data = maps.geocode(self.address)
            print(geocode_data)

            if geocode_data:
                self.latitude = geocode_data[0]['geometry']['location']['lat']
                self.longitude = geocode_data[0]['geometry']['location']['lng']
                print(f"Succesfully decode '{self.address}': Coordinates are {self.latitude}, {self.longitude}")
            else:
                self.latitude = None
                self.longitude = None
        except Exception as e:
            print(f"Error during geocoding for address '{self.address}': {e}")
            self.latitude = None
            self.longitude = None

    def reverse_geocode(self):
        """
        This method gets the approximate address for the provided longitude and latitude
        """
        try:
            maps = googlemaps.Client(key=os.getenv("GOOGLE_MAP_KEY"))
            address_data = maps.reverse_geocode(latlng=(self.latitude, self.longitude), result_type="street_address", location_type =["ROOFTOP"])
            
            if address_data:
                self.address = address_data[0]["formatted_address"]
                print(f"The coordinates - {self.longitude}, {self.latitude} point to this address approximately {self.address}")
        except Exception as e:
            print({"error":"Failed to find the address for the coordinates provided"})