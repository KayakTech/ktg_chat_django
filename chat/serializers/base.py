from django.conf import settings
from importlib import import_module
from typing import Type, Optional
from rest_framework.serializers import Serializer


def GET_SERIALIZER_FOR_OBJECT_TYPE(object_type: str) -> Optional[Type[Serializer]]:
    serializers_map = getattr(settings, 'OBJECT_TYPE_SERIALIZERS', {})
    serializer_config = serializers_map.get(object_type, {})

    serializer_path = serializer_config.get(
        'serializer') or serializer_config.get('serializers')

    if not serializer_path:
        return None

    try:
        module_name, serializer_name = serializer_path.rsplit('.', 1)
        module = import_module(module_name)
        return getattr(module, serializer_name)
    except (ImportError, AttributeError, ValueError):
        return None
