import aiohttp
import logging
from pydantic import BaseModel, Field
from env import env
from typing import Optional, Union

logger = logging.getLogger(__name__)


class User(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    created_at: str
    updated_at: str


class ApiResult(BaseModel):
    status: int
    message: str


class GetUserPayload(BaseModel):
    user_id: int


class GetUserResult(ApiResult):
    user: Optional[User] = Field(default=None)


class CreateChatPayload(BaseModel):
    chat_id: int
    chat_title: str
    chat_type: str
    chat_photo_url: Optional[str] = Field(default=None)


class CreateChatResult(ApiResult):
    pass


class CreateUserPayload(BaseModel):
    user_id: int
    first_name: str
    last_name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)


class CreateUserResult(ApiResult):
    pass


class AddMemberPayload(BaseModel):
    chat_id: int
    user_id: int
    first_name: str
    last_name: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)


class AddMemberResult(ApiResult):
    pass


class Chat(BaseModel):
    id: str
    title: str
    photo: str
    type: str
    thread_id: Optional[int] = Field(default=None)
    updated_at: str


class UpdateChatPayload(BaseModel):
    chat_id: int
    thread_id: Optional[int] = Field(default=None)
    title: Optional[str] = Field(default=None)
    photo: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)


class UpdateChatResult(ApiResult):
    chat: Optional[Chat] = Field(default=None)


class SendGroupReminderPayload(BaseModel):
    chat_id: int


class SendGroupReminderResult(ApiResult):
    message_id: Optional[int] = Field(default=None)
    timestamp: str
    reason: Optional[str] = Field(default=None)


class MigrateChatPayload(BaseModel):
    old_chat_id: int
    new_chat_id: int


class MigrateChatResult(ApiResult):
    pass


class Api:
    def __init__(self):
        self.default_headers = {"X-Api-Key": env.API_KEY}
        self.aio_session = aiohttp.ClientSession(
            base_url=env.API_BASE_URL,
            headers=self.default_headers,
        )

    async def get_user(
        self, payload: GetUserPayload
    ) -> Union[GetUserResult, Exception]:
        try:
            async with self.aio_session.get(f"user/{payload.user_id}") as response:
                data = await response.json()
                logger.debug(f"[API] GET user/{payload.user_id} response: {data}")
                response.raise_for_status()

                return GetUserResult(
                    user=User(
                        id=data.get("id"),
                        first_name=data.get("firstName"),
                        last_name=data.get("lastName"),
                        username=data.get("username"),
                        created_at=data.get("createdAt"),
                        updated_at=data.get("updatedAt"),
                    ),
                    status=response.status,
                    message="Success",
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(
                f"[API] GET user/{payload.user_id} - HTTP {e.status}: {e.message}"
            )
            if e.status == 404:
                return GetUserResult(
                    user=None,
                    status=e.status,
                    message="User not found",
                )
            return e
        except Exception as e:
            logger.error(f"[API] GET user/{payload.user_id} - Exception: {e}")
            return e

    async def create_user(
        self, payload: CreateUserPayload
    ) -> Union[CreateUserResult, Exception]:
        try:
            request_data = {
                "userId": payload.user_id,
                "firstName": payload.first_name,
                "lastName": payload.last_name,
                "userName": payload.username,
            }
            async with self.aio_session.post("user", json=request_data) as response:
                data = await response.json()
                logger.debug(f"[API] POST user response: {data}")
                response.raise_for_status()

                return CreateUserResult(
                    status=response.status,
                    message="User created successfully",
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(f"[API] POST user - HTTP {e.status}: {e.message}")
            return CreateUserResult(
                status=e.status, message=f"HTTP {e.status}: {e.message}"
            )
        except Exception as e:
            logger.error(f"[API] POST user - Exception: {e}")
            return e

    async def create_chat(
        self, payload: CreateChatPayload
    ) -> Union[CreateChatResult, Exception]:
        try:
            request_data = {
                "chatId": payload.chat_id,
                "chatTitle": payload.chat_title,
                "chatType": payload.chat_type,
                "chatPhoto": payload.chat_photo_url,
            }
            async with self.aio_session.post("chat", json=request_data) as response:
                data = await response.json()
                logger.debug(f"[API] POST chat response: {data}")
                response.raise_for_status()

                return CreateChatResult(
                    status=response.status,
                    message="Chat created successfully",
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(f"[API] POST chat - HTTP {e.status}: {e.message}")
            return CreateChatResult(
                status=e.status, message=f"HTTP {e.status}: {e.message}"
            )
        except Exception as e:
            logger.error(f"[API] POST chat - Exception: {e}")
            return e

    async def add_member(
        self, payload: AddMemberPayload
    ) -> Union[AddMemberResult, Exception]:
        try:
            async with self.aio_session.put(
                f"chat/{payload.chat_id}/members/{payload.user_id}",
            ) as response:
                data = await response.json()
                logger.debug(
                    f"[API] PUT chat/{payload.chat_id}/members/{payload.user_id} response: {data}"
                )
                response.raise_for_status()

                return AddMemberResult(
                    status=response.status,
                    message="Member added successfully",
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(
                f"[API] PUT chat/{payload.chat_id}/members/{payload.user_id} - HTTP {e.status}: {e.message}"
            )
            return AddMemberResult(
                status=e.status, message=f"HTTP {e.status}: {e.message}"
            )
        except Exception as e:
            logger.error(
                f"[API] PUT chat/{payload.chat_id}/members/{payload.user_id} - Exception: {e}"
            )
            return e

    async def update_chat(
        self, payload: UpdateChatPayload
    ) -> Union[UpdateChatResult, Exception]:
        try:
            request_data = {}
            if payload.thread_id is not None:
                request_data["threadId"] = payload.thread_id
            if payload.title is not None:
                request_data["title"] = payload.title
            if payload.photo is not None:
                request_data["photo"] = payload.photo
            if payload.type is not None:
                request_data["type"] = payload.type

            async with self.aio_session.patch(
                f"chat/{payload.chat_id}", json=request_data
            ) as response:
                data = await response.json()
                logger.debug(f"[API] PATCH chat/{payload.chat_id} response: {data}")
                response.raise_for_status()

                return UpdateChatResult(
                    chat=Chat(
                        id=data.get("id"),
                        title=data.get("title"),
                        photo=data.get("photo"),
                        type=data.get("type"),
                        thread_id=data.get("threadId"),
                        updated_at=data.get("updatedAt"),
                    ),
                    status=response.status,
                    message="Chat updated successfully",
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(
                f"[API] PATCH chat/{payload.chat_id} - HTTP {e.status}: {e.message}"
            )
            return UpdateChatResult(
                chat=None,
                status=e.status,
                message=f"HTTP {e.status}: {e.message}",
            )
        except Exception as e:
            logger.error(f"[API] PATCH chat/{payload.chat_id} - Exception: {e}")
            return e

    async def send_group_reminder(
        self, payload: SendGroupReminderPayload
    ) -> Union[SendGroupReminderResult, Exception]:
        try:
            request_data = {"chatId": str(payload.chat_id)}
            async with self.aio_session.post(
                "telegram/group-reminder/send", json=request_data
            ) as response:
                data = await response.json()
                logger.debug(f"[API] POST telegram/group-reminder/send response: {data}")
                response.raise_for_status()

                return SendGroupReminderResult(
                    status=response.status,
                    message="Group reminder sent successfully",
                    message_id=data.get("messageId"),
                    timestamp=data.get("timestamp"),
                    reason=data.get("reason"),
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(
                f"[API] POST telegram/group-reminder/send - HTTP {e.status}: {e.message}"
            )
            return SendGroupReminderResult(
                status=e.status,
                message=f"HTTP {e.status}: {e.message}",
                message_id=None,
                timestamp="",
                reason=f"HTTP error: {e.message}",
            )
        except Exception as e:
            logger.error(f"[API] POST telegram/group-reminder/send - Exception: {e}")
            return e

    async def migrate_chat(
        self, payload: MigrateChatPayload
    ) -> Union[MigrateChatResult, Exception]:
        try:
            request_data = {
                "oldChatId": payload.old_chat_id,
                "newChatId": payload.new_chat_id,
            }
            async with self.aio_session.patch(
                f"chat/{payload.old_chat_id}/migrate", json=request_data
            ) as response:
                data = await response.json()
                logger.debug(f"[API] PATCH chat/{payload.old_chat_id}/migrate response: {data}")
                response.raise_for_status()

                return MigrateChatResult(
                    status=response.status,
                    message="Chat migrated successfully",
                )
        except aiohttp.ClientResponseError as e:
            logger.warning(
                f"[API] PATCH chat/{payload.old_chat_id}/migrate - HTTP {e.status}: {e.message}"
            )
            return MigrateChatResult(
                status=e.status, message=f"HTTP {e.status}: {e.message}"
            )
        except Exception as e:
            logger.error(f"[API] PATCH chat/{payload.old_chat_id}/migrate - Exception: {e}")
            return e

    async def clean_up(self):
        await self.aio_session.close()
