import logging
import uuid
from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import List
from typing import Optional
from typing import Protocol
from typing import TypeVar
from urllib.parse import urlencode

import requests
from chat_sdk.schema import AttachmentSchema
from chat_sdk.schema import ChatResponse
from chat_sdk.schema import ChatSchema
from chat_sdk.schema import CreateAttachmentSchema
from chat_sdk.schema import ParticipantSchema
from chat_sdk.schema import RoomSchema

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResponseProtocol(Protocol, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int


@dataclass
class ChatClientConfig:
    base_url: str
    organisation_token: str
    timeout: int = 30
    max_retries: int = 3


class ChatClientException(Exception):
    """Base exception for chat client errors"""


class ChatClient:
    def __init__(self, config: ChatClientConfig):
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Authorization": f"Bearer {self.config.organisation_token}",
                "Content-Type": "application/json",
            }
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=self.config.max_retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _build_url(self, endpoint: str, params: Optional[dict] = None) -> str:
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if params:
            return f"{url}?{urlencode(params)}"
        return url

    def perform_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> Any:
        url = self._build_url(endpoint, params)
        try:
            response = self.session.request(
                method, url, json=data, files=files, timeout=self.config.timeout
            )
            response.raise_for_status()

            return response.json()

        except requests.HTTPError as e:
            try:
                error_data = e.response.json()
            except ValueError:
                error_data = {"detail": e.response.text}

            raise ChatClientException(error_data) from None

        except requests.RequestException as e:
            raise ChatClientException({"detail": str(e)}) from None

    # Room operations

    def create_room(self, data: RoomSchema) -> dict:
        return self.perform_request("POST", "/rooms/", data=data)

    def get_rooms(
        self, page: int = 1, size: int = 50, **filters: Any
    ) -> ResponseProtocol[RoomSchema]:
        params = {"page": page, "size": size, **filters}
        return self.perform_request("GET", "/rooms/", params=params)

    def get_room(
        self,
        room_id: uuid.UUID,
        participant_id: Optional[uuid.UUID] = None,
        last_n_messages: int = None,
        fetch_only: bool = False,
    ) -> RoomSchema:
        params = {}
        if participant_id:
            params["participant_id"] = participant_id
        if last_n_messages is not None:
            params["last_n_messages"] = last_n_messages
        if fetch_only:
            params["fetch_only"] = fetch_only

        return self.perform_request("GET", f"/rooms/{room_id}/", params=params)

    def update_room(self, room_id: uuid.UUID, data: RoomSchema) -> RoomSchema:
        return self.perform_request("PATCH", f"/rooms/{room_id}/", data=data)

    def delete_room(self, room_id: uuid.UUID, participant_id: uuid.UUID) -> None:
        self.perform_request("DELETE", f"/rooms/{room_id}/{participant_id}")

    def search_room(self, name: str = None, participant_email: str = None) -> None:
        params = {}

        if name:
            params["name"] = name

        if participant_email:
            params["participant_email"] = participant_email

        return self.perform_request("GET", "/rooms/search", params=params)

    # Chat operations
    def create_chat(self, data: ChatSchema) -> ChatResponse:
        return self.perform_request("POST", "/rooms/chats/", data=data)

    def update_chat(self, id, data: ChatSchema) -> ChatResponse:
        return self.perform_request("PATCH", f"/rooms/{id}/chats/", data=data)

    def get_chats_in_room(self, room_id: uuid.UUID, participant_id: uuid.UUID = None) -> ChatResponse:
        params = {}
        if participant_id:

            params["participant_id"] = participant_id
        return self.perform_request("GET", f"/rooms/{room_id}/chats/", params=params)

    def get_chat(self, id: uuid.UUID) -> ChatResponse:
        return self.perform_request("GET", f"/rooms/chats/{id}/")

    def delete_chat(self, id: uuid.UUID) -> None:
        return self.perform_request("DELETE", f"/rooms/{id}/chats")

    def search_chat(self, id: uuid.UUID, participant_id=uuid.UUID, content: str = None,
                    participant_email: str = None) -> None:
        params = {"participant_id": participant_id}

        if content:
            params["content"] = content

        if participant_email:
            params["participant_email"] = participant_email

        return self.perform_request("GET", f"/rooms/{id}/chats/search", params=params)

    def get_room_messages(
        self, room_id: uuid.UUID, page: int = 1, size: int = 50, **filters: Any
    ) -> ResponseProtocol[ChatResponse]:
        params = {"page": page, "size": size, **filters}
        return self.perform_request("GET", f"/rooms/{room_id}/chats/", params=params)

    def get_unread_messages(
        self, participant_id: uuid.UUID, page: int = 1, size: int = 50, **filters: Any
    ) -> ResponseProtocol[RoomSchema]:
        params = {"page": page, "size": size, **filters}
        return self.perform_request(
            "GET", f"/rooms/unread/{participant_id}/", params=params
        )

    def get_rooms_never_opened(
        self, participant_id: uuid.UUID, page: int = 1, size: int = 50, **filters: Any
    ) -> ResponseProtocol[RoomSchema]:
        params = {"page": page, "size": size, **filters}
        return self.perform_request(
            "GET", f"/rooms/{participant_id}/rooms-never-opened/", params=params
        )

    # Participant operations
    def add_participants(
        self, room_id: uuid.UUID, participants: List[ParticipantSchema]
    ) -> dict:
        data = participants
        return self.perform_request(
            "POST", f"/rooms/{room_id}/add-participant/", data=data
        )

    def add_participants_by_ids(
        self, room_id: uuid.UUID, participant_ids: list[uuid.UUID]
    ) -> dict:
        return self.perform_request(
            "POST", f"/rooms/{room_id}/add-participants-by-ids", data=participant_ids
        )

    def add_participants_by_emails(
        self, room_id: uuid.UUID, participant_emails: list[uuid.UUID]
    ) -> dict:
        return self.perform_request(
            "POST", f"/rooms/{room_id}/add-participants-by-emails", data=participant_emails
        )

    def remove_participant(self, room_id: uuid.UUID, participant_id: uuid.UUID) -> dict:
        return self.perform_request(
            "POST", f"/rooms/{room_id}/remove-participant/{participant_id}/"
        )

    def get_participant(self, id) -> ResponseProtocol[ParticipantSchema]:
        return self.perform_request("GET", f"/rooms/participant/{id}/")

    def generate_token_for_participant(
        self, participant_id
    ) -> ResponseProtocol[ParticipantSchema]:
        return self.perform_request("POST", f"/rooms/{participant_id}/generate-token/")

    def get_participants(
        self, room_id: uuid.UUID, page: int = 1, size: int = 50, **filters: Any
    ) -> ResponseProtocol[ParticipantSchema]:
        params = {"page": page, "size": size, **filters}
        return self.perform_request(
            "GET", f"/rooms/{room_id}/participants/", params=params
        )

    # Attachment operations

    def create_attachment(
        self, data: List[CreateAttachmentSchema]
    ) -> List[AttachmentSchema]:
        response = self.perform_request(
            "POST", "/rooms/attachments/", data=data)
        return [AttachmentSchema(**attachment) for attachment in response]

    def update_attachment(
        self, attachment_id: uuid.UUID, data: CreateAttachmentSchema
    ) -> AttachmentSchema:
        response = self.perform_request(
            "PUT", f"/rooms/attachments/{attachment_id}/", data=data
        )
        return AttachmentSchema(**response)

    def generate_presigned_url(self, attachment_id: str) -> AttachmentSchema:
        response = self.perform_request(
            "GET", f"rooms/attachments/{attachment_id}/generate-presigned-url/"
        )
        return AttachmentSchema(**response)

    def delete_attachment(self, attachment_id: uuid.UUID) -> None:
        self.perform_request("DELETE", f"rooms/attachments/{attachment_id}/")
