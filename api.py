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

    async def clean_up(self):
        await self.aio_session.close()
