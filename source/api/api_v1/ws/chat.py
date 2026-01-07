from fastapi import APIRouter, Depends, WebSocket
from starlette import status
from starlette.websockets import WebSocketDisconnect
from dishka import FromDishka, AsyncContainer
from dishka.integrations.fastapi import DishkaRoute, inject

from source.api.dependency.websocket.generation_pipe_abc import GenerationPipe
from source.db.models.choises.enum import MessageTypeChoises
from source.errors.general import GeneralCustomError
from source.schemas.pydantic.messages import WSMessageSimple
from source.schemas.other.internal_token import UserAuthData
from source.config.logging import logger
from source.services.gen_reg.generation_registry_abc import GenerationRegistry
from source.services.states.state_manager import StateManager
from source.services.websockets.websocket_manager import WebSocketConnectionManager
from source.api.dependency.auth.verify import get_websocket_headers_data


router = APIRouter(
    tags=["Agents"],
    prefix="/agents",
    route_class=DishkaRoute,
)


@router.websocket("/chat/")
@inject
async def chat_ws(
    websocket: WebSocket,
    container: FromDishka[AsyncContainer],
    headers: UserAuthData = Depends(get_websocket_headers_data),
):
    async with container() as request_container:
        websocket_manager = await request_container.get(WebSocketConnectionManager)
        state_manager = await request_container.get(StateManager)
        generation_registry = await request_container.get(GenerationRegistry)
        generation_pipe = await request_container.get(GenerationPipe)

        await websocket_manager.connect(user_id=headers.user_id, websocket=websocket)

        try:
            while True:
                data = await websocket.receive_json()

                if data.get("action") == "stop":
                    cancelled = await generation_registry.cancel(
                        user_id=str(headers.user_id)
                    )
                    await state_manager.clear_state(user_id=headers.user_id)

                    if cancelled:
                        await websocket_manager.send_message(
                            user_id=headers.user_id,
                            message=WSMessageSimple(
                                response_text="Остановлено. Состояние очищено.",
                                message_type=MessageTypeChoises.simple_message,
                            ),
                        )
                    else:
                        await websocket_manager.send_message(
                            user_id=headers.user_id,
                            message=WSMessageSimple(
                                response_text="Нет активной генерации для остановки.",
                                message_type=MessageTypeChoises.simple_message,
                            ),
                        )
                    continue

                generation_coroutine = generation_pipe.run_generation_pipeline(
                    data=data,
                    headers=headers,
                )

                await generation_registry.start(
                    user_id=str(headers.user_id),
                    generation_coroutine=generation_coroutine,
                )

        except GeneralCustomError as e:
            logger.info(f"GeneralCustomError in websocket: {str(e)}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=str(e))
        except WebSocketDisconnect:
            await generation_registry.cancel(str(headers.user_id))
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            logger.info(f"User {headers.user_id} disconnected")
