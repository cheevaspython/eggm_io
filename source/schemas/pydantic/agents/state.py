from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from source.types.model_id_uuid import ModelIdUuidType


class AgentType(Enum):
    """
    Типы агентов в системе
    """

    supervisor = "supervisor"
    reminder_agent = "reminder_agent"
    confirmation_agent = "confirmation_agent"
    edit_deal_agent = "edit_deal_agent"
    info_agent = "info_agent"  # для отображения информации

    def label(self):
        labels = {
            AgentType.supervisor: "Супервизор",
            AgentType.reminder_agent: "Агент напоминаний",
            AgentType.confirmation_agent: "Агент подтверждения",
            AgentType.edit_deal_agent: "Агент редактирования",
            AgentType.info_agent: "Информационный агент",
        }
        return labels[self]


class DealData(BaseModel):
    """
    Данные о сделке для агентов
    """

    crm_deal_id: int
    status: str
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    total_amount: Optional[float] = None
    delivery_date_from: Optional[datetime] = None
    delivery_date_to: Optional[datetime] = None
    loading_date: Optional[datetime] = None
    unloading_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    is_confirmed_by_manager: bool = False
    is_confirmed_by_director: bool = False
    comment: Optional[str] = None


class ApplicationData(BaseModel):
    """
    Данные о заявке для агентов
    """

    crm_application_id: int
    application_type: str  # buyer или seller
    client_name: Optional[str] = None
    delivery_date_from: Optional[datetime] = None
    delivery_date_to: Optional[datetime] = None
    total_eggs_count: Optional[int] = None
    price_per_egg: Optional[float] = None
    is_confirmed: bool = False
    comment: Optional[str] = None


class State(BaseModel):
    """
    Состояние для LangGraph агентов.
    Содержит всю информацию необходимую для обработки запроса пользователя.
    """

    # Пользователь
    telegram_user_id: ModelIdUuidType
    telegram_chat_id: int
    crm_user_id: int
    user_role: str

    # Входные данные
    user_input: Optional[str] = None
    user_command: Optional[str] = None  # /start, /help, /deals и т.д.

    # Тип задачи для маршрутизации
    agent_type: Optional[AgentType] = None

    # Данные для работы агентов
    deal_data: Optional[DealData] = None
    application_data: Optional[ApplicationData] = None

    # Результат работы агента
    result: Optional[str] = None
    needs_confirmation: bool = False
    confirmation_data: Optional[dict] = None

    # Дополнительный контекст
    additional_context: Optional[dict] = None

    # Метаданные
    message_id: Optional[int] = None  # ID сообщения в телеграм
    callback_data: Optional[str] = None  # Данные из inline кнопок


class SupervisorDecision(BaseModel):
    """
    Решение супервизора о маршрутизации
    """

    agent_type: AgentType
    reason: Optional[str] = None  # Причина выбора агента (для отладки)
