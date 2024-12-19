from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from chat.serializers import RoomResponseSerializer
from rest_framework import status
from chat.choices import OBJECT_TYPE

ROOM_SEARCH_SWAGGER_DOCS = swagger_auto_schema(
    operation_description="search room",
    responses={status.HTTP_200_OK: RoomResponseSerializer(many=True)},

    manual_parameters=[
        openapi.Parameter(
            "name",
            openapi.IN_QUERY,
            description="name",
            type=openapi.TYPE_STRING,

        ),
        openapi.Parameter(
            "email",
            openapi.IN_QUERY,
            description="email",
            type=openapi.TYPE_STRING,
        ),
    ],
)


CHAT_SEARCH_SWAGGER_DOCS = swagger_auto_schema(
    operation_description="search room",
    responses={},
    manual_parameters=[
        openapi.Parameter(
            "id",
            openapi.IN_QUERY,
            description="room id",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True

        ),
        openapi.Parameter(
            "participant_email",
            openapi.IN_QUERY,
            description="participant_email",
            type=openapi.TYPE_STRING,
        ),
        openapi.Parameter(
            "participant_id",
            openapi.IN_QUERY,
            description="participant id",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True
        ),



        openapi.Parameter(
            "content",
            openapi.IN_QUERY,
            description="content",
            type=openapi.TYPE_STRING,
        ),
    ],
)


ROOM_ID_QUERY_PARAM = openapi.Parameter(
    "room_id",
    openapi.IN_QUERY,
    description="room id",
    format=openapi.FORMAT_UUID,
    type=openapi.TYPE_STRING,
    required=True,
)

PARTICIPANT_ID_QUERY_PARAM = openapi.Parameter(
    "participant_id",
    openapi.IN_QUERY,
    description="participant id",
    format=openapi.FORMAT_UUID,
    type=openapi.TYPE_STRING,
    required=False,
)


LAST_N_MESSAGES_QUERY_PARAM = openapi.Parameter(
    "last_n_messages",
    openapi.IN_QUERY,
    description="Optional: Number of latest messages to retrieve",
    format=openapi.TYPE_NUMBER,
    type=openapi.TYPE_NUMBER,
    required=False,
)


CHAT_OBJECT_ID_QUERY_PARAM = openapi.Parameter(
    "object_id",
    openapi.IN_QUERY,
    description="object id",
    format=openapi.TYPE_STRING,
    type=openapi.TYPE_STRING,
    required=False,
)

CHAT_OBJECT_TYPE_QUERY_PARAM = openapi.Parameter(
    "object_type",
    openapi.IN_QUERY,
    description="Object Type",
    type=openapi.TYPE_STRING,
    enum=list(OBJECT_TYPE.ALL),
    required=False,
)
