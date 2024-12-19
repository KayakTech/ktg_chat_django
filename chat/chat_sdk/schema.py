import uuid
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import TypedDict


class Participant(TypedDict):
    name: str
    email: str
    data: Optional[dict[str, Any]]


class RoomSchema(TypedDict):
    name: str
    participants: List[Participant]
    is_archived: bool = False
    tag: List[str]


class ChatSchema(TypedDict):
    content: str
    room_id: uuid.UUID
    participant_id: uuid.UUID


class ChatResponse(TypedDict):
    content: str
    room_id: uuid.UUID
    created_by: Optional[Participant]


class ParticipantSchema(TypedDict):
    name: str
    email: str
    data: Optional[dict[str, Any]]


class ParticipantCreateAsListSchema(TypedDict):
    participants: List[ParticipantSchema]


class AttachmentSchema(TypedDict):
    url: str
    filename: str
    s3_key: str
    mime_type: str
    file_size: int
    created_by: uuid.UUID
    upload_finished_at: Optional[datetime]
    presigned_data: Optional[Dict[str, Any]]

    download_url: str = None


class CreateAttachmentSchema(TypedDict):
    filename: Optional[str]
    mime_type: Optional[str]
    participant_id: uuid.UUID
