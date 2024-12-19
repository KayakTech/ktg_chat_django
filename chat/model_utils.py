import uuid
import logging
from typing import Optional, Type

from django.apps import apps
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class ModelRetrievalService:

    @classmethod
    def get_model_by_name(cls, model_name: str) -> Optional[Type[models.Model]]:

        for app_config in apps.get_app_configs():
            try:
                model = apps.get_model(app_config.label, model_name)
                return model
            except LookupError:
                continue

        logger.warning(f"Model {model_name} not found in any installed apps")
        return None

    @classmethod
    def get_object_by_id(
        cls,
        object_id: uuid.UUID,
        models_to_search: Optional[list[str]] = None,
        **filters
    ) -> Optional[models.Model]:

        if models_to_search is None:
            models_to_search = getattr(settings, 'CHAT_MODELS', [])

        default_filters = {
            'id': object_id,

        }

        default_filters.update(filters)

        for model_name in models_to_search:
            try:
                model_class = cls.get_model_by_name(model_name)

                if not model_class:
                    continue

                object_type = model_class.objects.filter(
                    **default_filters).first()

                if object_type:
                    return object_type

            except Exception as e:
                logger.error(f"Error searching {model_name}: {e}")
                continue

        return None


def get_object_type_by_id(
    object_id: uuid.UUID,
    *args,
    **kwargs
) -> Optional[models.Model]:

    return ModelRetrievalService.get_object_by_id(object_id, *args, **kwargs)
