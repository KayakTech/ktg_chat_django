import uuid
import logging
from typing import Optional
from django.db import models

from chat.serializers.base import GET_SERIALIZER_FOR_OBJECT_TYPE

logger = logging.getLogger(__name__)


def get_object_type_by_id(
    object_id: uuid.UUID,
    object_type: str,
    *args,
    **kwargs
) -> Optional[models.Model]:

    serializer_class = GET_SERIALIZER_FOR_OBJECT_TYPE(object_type)

    model: models = serializer_class.Meta.model
    if not model:
        logger.error(f"failed to get model for {object_type}")
        return

    return model.objects.filter(id=object_id).first()
