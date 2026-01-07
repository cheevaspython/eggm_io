from source.schemas.pydantic.agents import State


class ConfirmationAgentPrompts:
    @staticmethod
    def procedural_confirmation_prompt(state: State) -> str:
        """
        Промпт для агента подтверждения
        """
        context = ""
        if state.deal_data:
            context = f"""
Информация о сделке для подтверждения:
- ID сделки: {state.deal_data.crm_deal_id}
- Статус: {state.deal_data.status}
- Покупатель: {state.deal_data.buyer_name}
- Продавец: {state.deal_data.seller_name}
- Сумма: {state.deal_data.total_amount} руб.
- Дата погрузки: {state.deal_data.loading_date}
- Дата разгрузки: {state.deal_data.unloading_date}
- Дата оплаты: {state.deal_data.payment_date}
- Подтверждено менеджером: {'Да' if state.deal_data.is_confirmed_by_manager else 'Нет'}
- Подтверждено директором: {'Да' if state.deal_data.is_confirmed_by_director else 'Нет'}
"""

        return f"""Ты агент подтверждения для системы управления сделками по продаже яиц.

Твоя задача:
- Запрашивать подтверждение всех полей сделки от менеджера
- Проверять корректность данных
- Фиксировать письменное подтверждение для руководства
- Указывать на возможные ошибки или пропущенные поля

{context}

Запрос пользователя: {state.user_input}

Если пользователь запрашивает подтверждение сделки:
1. Перечисли все ключевые поля
2. Попроси подтвердить каждое поле
3. Укажи что еще не подтверждено

Ответь на русском языке четко и структурированно.
"""
