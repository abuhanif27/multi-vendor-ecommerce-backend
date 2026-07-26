import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.urls import get_resolver

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
missing = []
for path, cls in set(all_views):
    if cls.__module__.startswith('django') or cls.__module__.startswith('rest_framework') or cls.__module__.startswith('drf_spectacular'):
        continue
        
    has_schema = hasattr(cls, '@extend_schema') or hasattr(cls, 'schema')
    if not has_schema:
        # Check if any methods have the decorator
        methods_with_schema = False
        for method_name in dir(cls):
            if not method_name.startswith('_'):
                method = getattr(cls, method_name)
                if hasattr(method, 'kwargs') and 'responses' in getattr(method, 'kwargs', {}):
                    methods_with_schema = True
                    break
                if hasattr(method, '__name__') and hasattr(cls, 'schema_view'):
                    methods_with_schema = True # rough heuristic
                    break
        
        # Checking if drf_spectacular decorated it
        # Actually a better check is to see if the file imports extend_schema
        # Let's just print all the view classes and we can cross-reference with grep
        pass

