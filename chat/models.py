
from django.db import models
from django.conf import settings
import uuid
from chat.choices import OBJECT_TYPE


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_deleted = models.BooleanField(default=False)
    name = models.CharField(max_length=200)
    room_id = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    object_id = models.CharField(max_length=500)
    object_type = models.CharField(
        max_length=200, choices=OBJECT_TYPE.get_choices())
    tags = models.JSONField(default=list, blank=True)
    is_archived = models.BooleanField(default=False)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def object_instance(self):
        from chat.model_utils import get_object_type_by_id

        return get_object_type_by_id(self.object_id)
