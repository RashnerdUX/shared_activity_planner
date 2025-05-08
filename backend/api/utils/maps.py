import googlemaps
import dotenv
import os
import json
import hashlib

from django.core.cache import cache

dotenv.load_dotenv()
def geocode_with_cache(address):
    """
    This utility function helps me to geocode addresses and caches them for 24 hours to limit calls to Google Maps API
    """
    # Create a consistent cache key from the address
    key = f"geocode:{hashlib.md5(address.strip().lower().encode()).hexdigest()}"

    # Return cached result if cached
    cached_result = cache.get(key)
    if cached_result:
        return json.loads(cached_result)

    maps = googlemaps.Client(key=os.getenv("GOOGLE_MAP_KEY"))
    result = maps.geocode(address)

    # Cache result for 24 hours
    if result:
        cache.set(key, json.dumps(result), timeout=60 * 60 * 24)

    return result