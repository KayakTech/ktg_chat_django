from rest_framework.response import Response
from rest_framework import status
from uuid import UUID
from chat.serializers import ParticipantSerializer
from chat.serializers import ChatCreateSerializer
from chat.serializers import AttachmentResponseSerializer, ChatResponseSerializer
from chat.serializers import RoomCreateSerializer, AttachmentCreateSerializer
from chat.serializers import AttachmentPresignedDataeSerializer
from chat.serializers import ChatRoomCreateSerializer, ParticipantIdsListSerializer
from chat.serializers import ChatRoomResponseSerializer
from chat.service import chat_client
from chat.service import ChatService as chat_service
from drf_yasg.utils import swagger_auto_schema
from chat.api_docs import ROOM_SEARCH_SWAGGER_DOCS, CHAT_SEARCH_SWAGGER_DOCS
from chat.api_docs import ROOM_ID_QUERY_PARAM, PARTICIPANT_ID_QUERY_PARAM
from chat.api_docs import LAST_N_MESSAGES_QUERY_PARAM
from chat.api_docs import CHAT_OBJECT_ID_QUERY_PARAM, CHAT_OBJECT_TYPE_QUERY_PARAM
from rest_framework.request import Request
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated


class BaseFilterParams:
    def filter_query_params(self, allowed_params):
        return {k: v for k, v in self.request.query_params.items() if k in allowed_params}


class BaseView(viewsets.ViewSet):

    def get_context(self, *args, **kwargs):
        return {'request': self.request}


class RoomView(BaseFilterParams, BaseView):

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: ChatRoomResponseSerializer(many=True)},
        manual_parameters=[
            LAST_N_MESSAGES_QUERY_PARAM, CHAT_OBJECT_ID_QUERY_PARAM, CHAT_OBJECT_TYPE_QUERY_PARAM
        ]

    )
    @action(detail=False,
            methods=["get"],  permission_classes=[IsAuthenticated])
    def get_rooms(self, request: Request, *args, **kwargs):

        allowed_params = ['object_id', 'object_type']
        query_params = self.filter_query_params(allowed_params)

        chat_rooms = chat_service.get_chat_rooms_for_user(
            user=request.user, filters=query_params)

        serializer = ChatRoomResponseSerializer(
            chat_rooms, many=True, context=self.get_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=ChatRoomCreateSerializer,
        responses={status.HTTP_201_CREATED: ChatRoomResponseSerializer},
    )
    @action(detail=False,
            methods=["post"],  permission_classes=[IsAuthenticated])
    def create_room(self, request, *args, **kwargs):
        request.data['created_by'] = self.request.user

        serializer = ChatRoomCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        room = chat_service.create_chat_room(
            **request.data
        )

        serializer = ChatRoomResponseSerializer(
            room, context=self.get_context())

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method="patch",
        request_body=RoomCreateSerializer,
        responses={status.HTTP_200_OK: ChatRoomResponseSerializer},
    )
    @action(detail=True,
            methods=["patch"],  permission_classes=[IsAuthenticated])
    def update_room(self, request, pk: UUID = None, *args, **kwargs):
        instance = chat_service.get_chat_room(pk)
        serializer = RoomCreateSerializer(
            data=request.data, instance=instance, partial=True)

        serializer.is_valid(raise_exception=True)

        updated_room = chat_service.update_chat_room(
            id=pk, kwargs=request.data)

        serializer = ChatRoomResponseSerializer(
            updated_room, context=self.get_context())

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: ChatRoomResponseSerializer},
        manual_parameters=[LAST_N_MESSAGES_QUERY_PARAM]
    )
    @action(detail=True,
            methods=["get"],  permission_classes=[IsAuthenticated])
    def get_room(self, request, pk: UUID = None, *args, **kwargs):

        rooms = chat_service.get_chat_room(pk)
        serializer = ChatRoomResponseSerializer(
            rooms, context=self.get_context())
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='delete',
        operation_description="participant id",
        responses={},
        manual_parameters=[],
    )
    @action(detail=True,
            methods=["delete"],
            permission_classes=[IsAuthenticated])
    def delete_room(self, request, pk: UUID = None, *args, **kwargs):

        chat = chat_service.get_chat_room(pk)

        participant_id = chat_service.get_chat_client_participant_id(
            room_id=chat.room_id, user_email=request.user.email
        )

        chat = chat_service.get_chat_room(pk)

        chat_service.remove_participants(
            id=chat.id, participant_ids=[request.user.id])

        chat_client.delete_room(
            room_id=chat.room_id, participant_id=participant_id)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @ROOM_SEARCH_SWAGGER_DOCS
    @action(detail=False,
            methods=["get"],
            permission_classes=[IsAuthenticated])
    def search_room(self, request, *args, **kwargs):

        allowed_params = ['name', 'email']
        query_params = self.filter_query_params(allowed_params)

        if 'email' in query_params:
            query_params['participants__email'] = query_params.pop('email')

        rooms = chat_service.get_chat_rooms_for_user(
            user=request.user, filters=query_params)

        serializer = ChatRoomResponseSerializer(
            rooms, context=self.get_context(), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatView(BaseFilterParams, viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=ChatCreateSerializer,
        responses={status.HTTP_201_CREATED: ChatResponseSerializer},
    )
    @action(detail=False,
            methods=["post"],
            permission_classes=[IsAuthenticated])
    def create_chat(self, request,  *args, **kwargs):
        serializer = ChatCreateSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        try:
            chat_data = serializer.data
            created_chat = chat_client.create_chat(chat_data)
            serializer = ChatResponseSerializer(created_chat)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method="get",
        operation_description="Get chats in a room by participant_id and room_id",
        responses={status.HTTP_200_OK: ChatResponseSerializer(many=True)},
        manual_parameters=[ROOM_ID_QUERY_PARAM, PARTICIPANT_ID_QUERY_PARAM],
    )
    @action(detail=False,
            methods=["get"],
            permission_classes=[IsAuthenticated])
    def chats_in_room(self, request, *args, **kwargs):

        allowed_params = ['room_id', 'participant_id']
        query_params = self.filter_query_params(allowed_params)

        chats = chat_client.get_chats_in_room(**query_params)
        serializer = ChatResponseSerializer(chats["items"], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method="get",
        responses={status.HTTP_200_OK: ChatResponseSerializer},
    )
    @action(detail=True,
            methods=["get"],  permission_classes=[IsAuthenticated])
    def get_chat(self, request, pk: UUID = None, *args, **kwargs):

        chat = chat_client.get_chat(id=pk, )
        serializer = ChatResponseSerializer(chat)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=ChatCreateSerializer(),
        responses={status.HTTP_200_OK: ChatResponseSerializer},
    )
    @action(detail=True,
            methods=["patch"],
            permission_classes=[IsAuthenticated])
    def update_chat(self, request, pk: UUID, *args, **kwargs):

        serializer = ChatCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        chat_data = serializer.data
        updated_chat = chat_client.update_chat(id=pk, data=chat_data)
        serializer = ChatResponseSerializer(updated_chat)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True,
            methods=["delete"],
            permission_classes=[IsAuthenticated])
    def delete_chat(self, request, pk: UUID, *args, **kwargs):

        try:
            chat_client.delete_chat(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @CHAT_SEARCH_SWAGGER_DOCS
    @action(detail=False,
            methods=["get"],
            permission_classes=[IsAuthenticated])
    def search_chat(self, request, *args, **kwargs):

        allowed_params = ['id', 'participant_id',
                          'participant_email', 'content']
        query_params = self.filter_query_params(allowed_params)

        try:

            result = chat_client.search_chat(**query_params)

            serializer = ChatResponseSerializer(result['items'], many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ParticipantView(BaseFilterParams, viewsets.ViewSet):

    @swagger_auto_schema(
        method="get",

        responses={
            status.HTTP_200_OK: ParticipantSerializer(many=True)},
        manual_parameters=[ROOM_ID_QUERY_PARAM]
    )
    @action(detail=False,
            methods=["get"],
            permission_classes=[IsAuthenticated])
    def get_participants(self, request, *args, **kwargs):
        allowed_params = ['room_id']
        query_params = self.filter_query_params(allowed_params)
        participants = chat_client.get_participants(**query_params)
        serializer = ParticipantSerializer(
            participants["items"], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(

        operation_description="Add Existing  participants to a room",
        request_body=ParticipantIdsListSerializer,
        responses={
            status.HTTP_200_OK: ParticipantSerializer(many=True)},
        manual_parameters=[ROOM_ID_QUERY_PARAM]
    )
    @action(detail=False,
            methods=["post"],
            permission_classes=[IsAuthenticated])
    def create_participants_by_ids(self, request, *args, **kwargs):
        allowed_params = ['room_id']
        query_params = self.filter_query_params(allowed_params)

        try:

            serializer = ParticipantIdsListSerializer(
                data=request.data)

            serializer.is_valid(raise_exception=True)

            participant_ids = serializer.data.get('participant_ids')

            added_participants = chat_client.add_participants_by_ids(
                **query_params, participant_ids=participant_ids)

            serializer = ParticipantSerializer(
                added_participants["participants"], many=True)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(

        responses={
            status.HTTP_204_NO_CONTENT: None},
        manual_parameters=[ROOM_ID_QUERY_PARAM, PARTICIPANT_ID_QUERY_PARAM]
    )
    @action(detail=False,
            methods=["delete"],
            permission_classes=[IsAuthenticated])
    def remove_participant(self, *args, **kwargs):
        allowed_params = ['room_id', 'participant_id']
        query_params = self.filter_query_params(allowed_params)

        try:
            removed_participant = chat_client.remove_participant(
                **query_params)

            return Response(data=removed_participant, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AttachmentView(BaseFilterParams, viewsets.ViewSet):

    @swagger_auto_schema(
        request_body=AttachmentCreateSerializer(many=True),
        responses={
            status.HTTP_201_CREATED: AttachmentPresignedDataeSerializer(many=True)},
    )
    @action(detail=False,
            methods=["post"],
            permission_classes=[IsAuthenticated])
    def create_attachment(self, request, *args, **kwargs):
        serializer = AttachmentCreateSerializer(
            data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        attachment_data = serializer.data
        created_attachment = chat_client.create_attachment(attachment_data)

        return Response(created_attachment, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        request_body=AttachmentCreateSerializer(),
        responses={
            status.HTTP_200_OK: AttachmentPresignedDataeSerializer(many=True)},
    )
    @action(detail=True,
            methods=["patch"],
            permission_classes=[IsAuthenticated])
    def update_attachment(self, request, pk: UUID, *args, **kwargs):

        serializer = AttachmentCreateSerializer(
            data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        chat_data = serializer.data
        updated_chat = chat_client.update_attachment(
            attachment_id=pk, data=chat_data)
        serializer = AttachmentResponseSerializer(updated_chat)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        responses={
            status.HTTP_200_OK: AttachmentResponseSerializer},
    )
    @action(detail=True,
            methods=["post"],
            permission_classes=[IsAuthenticated])
    def generate_presigned_url(self, request, pk: UUID, *args, **kwargs):

        try:
            attachment = chat_client.generate_presigned_url(attachment_id=pk)
            serializer = AttachmentResponseSerializer(attachment)

            return Response(data=serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=["delete"],
            permission_classes=[IsAuthenticated])
    def delete_attachment(self, pk: UUID, *args, **kwargs):

        chat_client.delete_attachment(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
