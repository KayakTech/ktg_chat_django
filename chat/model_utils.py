from chat.choices import OBJECT_TYPE
from rest_framework.serializers import Serializer
from typing import Type, Optional
from importlib import import_module
from django.conf import settings
import uuid
import logging
from django.db import models


logger = logging.getLogger(__name__)


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


def get_object_type_by_id(
    object_id: uuid.UUID,
    object_type: str,
) -> Optional[models.Model]:

    serializer_class = GET_SERIALIZER_FOR_OBJECT_TYPE(object_type)
    if not serializer_class:
        logger.error(f"failed to get serializer_class for {object_type}")
        return None

    model: models.Model = serializer_class.Meta.model
    if not model:
        logger.error(f"failed to get model for {object_type}")
        return

    return model.objects.filter(id=object_id).first()
