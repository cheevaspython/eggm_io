from enum import Enum


class InlineStatusChoises(Enum):
    confirmed = "confirmed"
    rejected = "rejected"
    needs_confirmation = "needs_confirmation"
    select_date = "select_date"

    def label(self):
        labels = {
            InlineStatusChoises.confirmed: "Подтверждено",
            InlineStatusChoises.rejected: "Отклоненный",
            InlineStatusChoises.needs_confirmation: "Требует подтверждения",
            InlineStatusChoises.select_date: "Выбрать дату",
        }
        return labels[self]


class MessageTypeChoises(Enum):
    simple_message = "simple_message"
    deal_analyze = "deal_analyze"
    error = "error"

    def label(self):
        labels = {
            MessageTypeChoises.simple_message: "Простое сообщение",
            MessageTypeChoises.deal_analyze: "Анализ сделки",
            MessageTypeChoises.error: "Ошибка",
        }
        return labels[self]


class RoleTypeChoises(Enum):
    manager_sell = "1"
    manager_buy = "2"
    manager_sell_and_buy = "3"
    logic = "4"
    manager_way = "5"
    money_manager = "6"
    accountant = "7"
    super_user = "8"
    manager_admin = "9"
    guest = "10"
    office_manager = "11"
    one_c_api = "12"
    lawyer = "13"

    def label(self):
        labels = {
            RoleTypeChoises.manager_sell: "Менеджер продажа",
            RoleTypeChoises.manager_buy: "Менеджер покупка",
            RoleTypeChoises.manager_sell_and_buy: "Менеджер покупка продажа",
            RoleTypeChoises.logic: "Логист",
            RoleTypeChoises.manager_way: "Менеджер направления",
            RoleTypeChoises.money_manager: "Фин директор",
            RoleTypeChoises.accountant: "Бухгалтер",
            RoleTypeChoises.super_user: "Cупер юзер",
            RoleTypeChoises.manager_admin: "Менеджер администратор",
            RoleTypeChoises.guest: "Гость",
            RoleTypeChoises.office_manager: "Офис менеджер",
            RoleTypeChoises.one_c_api: "1c API",
            RoleTypeChoises.lawyer: "Юрист",
        }
        return labels[self]


class PermissionStatus(Enum):
    standart = "1"
    extended = "2"

    def label(self):
        labels = {
            PermissionStatus.standart: "Стандартный",
            PermissionStatus.extended: "Расширенный",
        }
        return labels[self]


class TaskTypeChoises(Enum):
    confirm_agent = "confirm_agent"
    edit_deal_agent = "edit_deal_agent"
    reminder_agent = "reminder_agent"

    def label(self):
        labels = {
            TaskTypeChoises.confirm_agent: "Агент подтверждения",
            TaskTypeChoises.edit_deal_agent: "Агент редактирования сделок",
            TaskTypeChoises.reminder_agent: "Агент напоминаний",
        }
        return labels[self]
