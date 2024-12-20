from typing import List, Optional, Dict
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from chat.models import ChatRoom
from chat.chat_sdk.ktg_chat_client import ChatClientConfig, ChatClient
from django.conf import settings
from django.db.models import Q
from uuid import UUID
from chat.model_utils import get_object_type_by_id


class ChatValidationError(ValidationError):
    pass


class ChatService:

    config = ChatClientConfig(settings.CHAT_API_BASE_URL,
                              settings.CHAT_ORGANISATION_TOKEN)
    chat_client = ChatClient(config)

    def get_participants(self, participant_ids: List[str]) -> ChatRoom:
        participants = get_user_model().objects.filter(
            id__in=participant_ids)

        return participants

    def archived_chats(self, user) -> ChatRoom:
        archived_chats = ChatRoom.objects.filter(
            Q(created_by=user) | Q(participants=user)).distinct()

        return archived_chats.filter(is_archived=True)

    def create_chat_room(self, **kwargs) -> ChatRoom:

        created_by = kwargs.pop('created_by')
        original_kwargs = kwargs.copy()

        object_id = kwargs.get('object_id')
        participants_data = kwargs.pop('participants', [])

        created_by_info = {
            'email': created_by.email,
            'name': created_by.get_full_name() or created_by.email
        }

        original_kwargs['participants'].append(created_by_info)
        participants_data.append(created_by_info)

        tags = kwargs.get('tags', [])

        participant_emails = [p['email']
                              for p in participants_data if 'email' in p]

        existing_chat_room = ChatRoom.objects.filter(
            object_id=object_id,
            tags=tags,
            is_deleted=False,
            participants__email__in=participant_emails
        ).distinct().first()

        if existing_chat_room:
            return existing_chat_room

        chat_room = ChatRoom(**kwargs, created_by=created_by)

        client_chat_room = self.chat_client.create_room(original_kwargs)

        chat_room.room_id = client_chat_room.get('id', None)

        with transaction.atomic():
            chat_room.save()

            self.get_or_create_participant(chat_room, participants_data)

        return chat_room

    def get_or_create_participant(self, chat_room: ChatRoom, participants_data: List[dict]):
        created_by = chat_room.created_by
        if created_by and created_by not in chat_room.participants.all():
            chat_room.participants.add(created_by)
            chat_room.save()

        for participant_data in participants_data:
            email = participant_data.get('email')
            name = participant_data.get('name', email)

            if not email:
                raise ValidationError(
                    "Email is required for creating or retrieving a participant.")

            user, _ = get_user_model().objects.get_or_create(
                email=email,
                defaults={'username': email,
                          'first_name': name, 'last_name': name}
            )

            if user not in chat_room.participants.all():
                chat_room.participants.add(user)
                chat_room.save()

        return user

    def get_participant_ids_info_by_ids(self, participant_ids: List[str], data: dict = None) -> List[Dict[str, str]]:

        users = get_user_model().objects.filter(id__in=participant_ids)

        users_info = [
            {
                'email': user.email,
                'name': user.get_full_name() or user.email,

            }
            for user in users
        ]

        return users_info

    def get_chat_room(self, id: str) -> ChatRoom:

        return ChatRoom.objects.filter(id=id).first()

    def update_chat_room(self, id: str, **kwargs) -> ChatRoom:
        chat = self.get_chat_room(id)

        update_data = kwargs.get('kwargs', {})

        participants = update_data.pop('participants', None)

        for key, value in update_data.items():
            setattr(chat, key, value)

        if participants:
            self.get_or_create_participant(chat, participants)

        update_data['participants'] = participants

        with transaction.atomic():
            self.chat_client.update_room(
                room_id=chat.room_id, data=update_data
            )
            chat.save()

        return chat

    def delete_chat_room(self, id: str) -> None:

        chat = self.get_chat_room(id)
        chat.delete()

    def add_participants(self, id: str, participant_ids: List[str]) -> ChatRoom:

        chat = self.get_chat_room(id)

        participants = self.get_participants(participant_ids)

        chat.participants.add(*participants)
        chat.save()

        return chat

    def get_chat_rooms_for_user(

        self, user, filters: Optional[Dict[str, any]] = None
    ) -> List['ChatRoom']:
        query = Q(created_by=user) | Q(participants=user)
        query &= Q(is_deleted=False)

        if filters:
            for key, value in filters.items():
                query &= Q(**{f"{key}__icontains": value})

        return ChatRoom.objects.filter(query).distinct()

    def remove_participants(self, id: str, participant_ids: List[str]) -> ChatRoom:

        chat = self.get_chat_room(id)

        participants = self.get_participants(participant_ids)

        chat.participants.remove(*participants)
        chat.save()

        if not chat.participants.exists():
            chat.delete()

        return chat

    def bulk_add_participants(self, id: List[str], participant_ids: List[str]) -> None:

        chats: ChatRoom = ChatRoom.objects.filter(id__in=id)
        participants = self.get_participants(participant_ids)

        for chat in chats:
            chat: ChatRoom
            chat.participants.add(*participants)
        chats.save()

    def get_chat_client_participant_by_email(
        self, room_id: UUID, user_email: str
    ) -> Optional[dict]:
        try:
            participants = self.chat_client.get_participants(
                room_id=room_id, email=user_email).get('items', [])

            return next((p for p in participants if p.get('email') == user_email), None)
        except Exception:
            return None

    def get_chat_client_participant_id(
        self, room_id: UUID, user_email: str
    ) -> Optional[dict]:

        participant = self.get_chat_client_participant_by_email(
            room_id, user_email)

        if not participant:
            return
        return participant.get('id')

    def get_chat_client_id_from_chat_room(
        self, id: UUID
    ) -> ChatRoom:

        chat = self.get_chat_room(id)

        return chat.room_id or id

    def get_object_type_by_id(self, id: UUID, object_type: str):
        return get_object_type_by_id(id, object_type)


chat_service = ChatService()
