import json
from django.core.cache import cache

def set_cache(key, data, time):
    cache.set(key, json.dumps(data), timeout=time)

def get_cache(key):
    cached_data = cache.get(key)
    if cached_data:
        return json.loads(cached_data) 
    return None

def remove_cache(key):
    cache.delete(key)
