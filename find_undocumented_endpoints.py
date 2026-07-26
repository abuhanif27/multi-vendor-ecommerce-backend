import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema

generator = SchemaGenerator()
schema = generator.get_schema()

# schema['paths'] contains all the documented endpoints.
# The user wants "do rest of the all the swagers doc". 
# The best way is to go through the apps and just apply @extend_schema to everything that misses it.
