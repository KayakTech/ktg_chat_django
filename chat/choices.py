from django.conf import settings


class OBJECT_TYPE:

    ALL = [model.lower() for model in settings.CHAT_MODELS]

    @classmethod
    def get_choices(cls):
        return [
            (model, model.capitalize())
            for model in cls.ALL
        ]

    @classmethod
    def get_exact_key(cls, object_type: str):
        for model in settings.CHAT_MODELS:

            if model.lower() == object_type.lower():

                return model
        return None
