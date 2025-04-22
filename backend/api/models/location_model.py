from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(blank=True)
    longitude = models.FloatField(blank=True)
    details = models.TextField()

    def __str__(self):
        return f"{self.name} can be found at {self.address}"
    
