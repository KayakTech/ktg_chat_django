from django.conf import settings
from importlib import import_module
from typing import Type, Optional
from rest_framework.serializers import Serializer
from chat.choices import OBJECT_TYPE


def GET_SERIALIZER_FOR_OBJECT_TYPE(object_type: str) -> Optional[Type[Serializer]]:
    serializers_map = getattr(settings, 'OBJECT_TYPE_SERIALIZERS', {})

    exact_key = OBJECT_TYPE.get_exact_key(object_type)
    if not exact_key:
        return None

    serializer_config = serializers_map.get(exact_key, {})

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
