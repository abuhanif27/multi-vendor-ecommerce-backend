import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.urls import get_resolver
from drf_spectacular.utils import extend_schema

resolver = get_resolver()

def extract_views(urlpatterns, prefix=''):
    views = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            views.extend(extract_views(pattern.url_patterns, prefix + str(pattern.pattern)))
        else:
            if hasattr(pattern.callback, 'view_class'):
                views.append((prefix + str(pattern.pattern), pattern.callback.view_class))
            elif hasattr(pattern.callback, 'cls'):
                views.append((prefix + str(pattern.pattern), pattern.callback.cls))
    return views

all_views = extract_views(resolver.url_patterns)
for path, cls in set(all_views):
    if not cls.__module__.startswith('django') and not cls.__module__.startswith('rest_framework'):
        print(f"{cls.__module__}.{cls.__name__}")
