from rest_framework import serializers
from chat.models import ChatRoom
from chat.service import chat_client
from django.contrib.auth import get_user_model
from chat.service import ChatService as chat_service
from rest_framework.request import Request
from drf_yasg.utils import swagger_serializer_method
from chat.serializers.base import GET_SERIALIZER_FOR_OBJECT_TYPE


class ChatUserAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        exclude = ['password', 'groups', 'user_permissions']


class ParticipantSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=False)
    email = serializers.EmailField()
    token = serializers.CharField(required=False, read_only=True)
    timezone = serializers.CharField(default="UTC")
    data = serializers.JSONField(required=False)


class ParticipantIdsListSerializer(serializers.Serializer):
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )


class ParticipantEmailsListSerializer(serializers.Serializer):
    participant_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=True
    )


class ChatCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False)
    room_id = serializers.UUIDField()
    participant_id = serializers.UUIDField()
    attachments = serializers.ListField(
        child=serializers.UUIDField(), required=False)


class RoomCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    participants = ParticipantSerializer(many=True, required=True)
    is_archived = serializers.BooleanField(default=False)

    def validate_participants(self, value):

        if self.instance is None:
            if len(value) < 2:
                raise serializers.ValidationError(
                    "At least two participants must be provided.")
            return value


class RoomResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    name = serializers.CharField(required=False, default="")
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    organisation_id = serializers.UUIDField(required=False)
    unread_count = serializers.IntegerField(default=0)
    participants = ParticipantSerializer(many=True)
    is_archived = serializers.BooleanField(default=False)
    last_chat = ChatCreateSerializer(many=True, required=False)
    unread_participants = serializers.ListField(
        child=serializers.DictField(), required=False)
    dormant_participants = serializers.ListField(
        child=serializers.DictField(), required=False)


class AttachmentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    url = serializers.URLField()
    filename = serializers.CharField()
    s3_key = serializers.CharField()
    mime_type = serializers.CharField()
    file_size = serializers.IntegerField()
    created_by = serializers.UUIDField(required=False)
    upload_finished_at = serializers.DateTimeField(required=False)
    presigned_data = serializers.JSONField(required=False)
    thumbnail = serializers.CharField(required=False)
    download_url = serializers.URLField()


class ChatResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=False)
    content = serializers.CharField(required=False)
    room_id = serializers.UUIDField(required=False)
    created_by = ParticipantSerializer(required=False)
    attachments = AttachmentResponseSerializer(many=True, required=False)


class AttachmentCreateSerializer(serializers.Serializer):
    filename = serializers.CharField(required=True)
    mime_type = serializers.CharField(required=False)
    participant_id = serializers.UUIDField()


class PresignedData(serializers.Serializer):
    url = serializers.URLField()
    acl = serializers.CharField(default='public-read')
    content_type = serializers.CharField()
    key = serializers.CharField()
    x_amz_algorithm = serializers.CharField()
    x_amz_credential = serializers.CharField()
    x_amz_date = serializers.CharField()
    policy = serializers.CharField()
    x_amz_signature = serializers.CharField()


class AttachmentPresignedDataeSerializer(AttachmentResponseSerializer):

    PresignedData = PresignedData()


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    is_archived = serializers.BooleanField(default=False)
    participants = ParticipantSerializer(many=True)

    class Meta:
        model = ChatRoom
        exclude = ['is_deleted']

        read_only_fields = [
            "id",
            "created_by",
            "room_id",
        ]

    def validate_participants(self, value):

        if len(value) < 2:

            raise serializers.ValidationError(
                code="invalid_participant",
                detail="At least two participants must be provided.")
        return value

    def validate_object_id(self, value):
        from chat.model_utils import get_object_type_by_id

        object_id = get_object_type_by_id(value)

        if not object_id:
            raise serializers.ValidationError(
                code="invalid_object_id",
                detail="invalid object_id provided")
        return value


class ChatRoomResponseSerializer(serializers.ModelSerializer):
    created_by = ChatUserAccountSerializer()
    object_type_summary = serializers.SerializerMethodField()
    room_details = serializers.SerializerMethodField()
    participant_id = serializers.CharField(required=False)

    class Meta:
        model = ChatRoom
        exclude = ['is_deleted', 'participants']

        read_only_fields = [
            "id",
            "created_by"
        ]

    @swagger_serializer_method(serializer_or_field=RoomResponseSerializer)
    def get_room_details(self, obj: ChatRoom):

        request: Request = self.context['request']
        user = request.user

        last_n_messages = request.query_params.get('last_n_messages', 1)

        participant_id = chat_service.get_chat_client_participant_id(
            room_id=obj.room_id, user_email=user.email)

        if not participant_id or not obj.room_id:
            return {}

        self.fields['participant_id'].default = participant_id

        room_details = chat_client.get_room(
            room_id=obj.room_id,
            last_n_messages=last_n_messages,
            participant_id=participant_id,
            fetch_only=self.context.get('fetch_only', True)
        )

        return RoomResponseSerializer(room_details).data

    def get_object_type_summary(self, obj: ChatRoom):

        serializer_class = GET_SERIALIZER_FOR_OBJECT_TYPE(obj.object_type_name)

        if not obj.object_instance or not serializer_class:
            return {}

        return serializer_class(obj.object_instance).data
