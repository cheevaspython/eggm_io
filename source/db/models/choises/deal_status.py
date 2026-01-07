from enum import Enum


class DealStatus(Enum):
    """
    Статусы сделки (синхронизированы с Django CRM)
    """

    calculation = 1  # Просчет
    confirmed_calculation = 2  # Подтвержденный просчет
    deal = 3  # Сделка
    closed_deal = 4  # Закрытая сделка

    def label(self):
        labels = {
            DealStatus.calculation: "Просчет",
            DealStatus.confirmed_calculation: "Подтвержденный просчет",
            DealStatus.deal: "Сделка",
            DealStatus.closed_deal: "Закрытая сделка",
        }
        return labels[self]


class DealDetailStatus(Enum):
    """
    Детальный статус сделки
    """

    not_confirmed = 0  # не подтверждена
    waiting_fin_director = 1  # на подтверждении у фин. директора
    waiting_payment_base = 2  # на ожидании основания платежа от продавца
    waiting_fin_director_payment = 3  # на подтверждении у фин. директора (по оплате счета от продавца)
    payment_process = 4  # в процессе оплаты основания платежа
    loading = 5  # на погрузке и ожидании УПД от продавца
    in_transit = 6  # товар в пути
    waiting_outgoing_upd = 7  # на ожидании загрузки исходящей УПД бухгалтером
    unloading_control = 8  # на контроле разгрузки
    docs_check = 9  # на проверке загруженных документов бухгалтером
    waiting_full_payment = 10  # на ожидании полной оплаты покупателем
    closed = 11  # сделка закрыта

    def label(self):
        labels = {
            DealDetailStatus.not_confirmed: "Не подтверждена",
            DealDetailStatus.waiting_fin_director: "На подтверждении у фин. директора",
            DealDetailStatus.waiting_payment_base: "Ожидание основания платежа от продавца",
            DealDetailStatus.waiting_fin_director_payment: "На подтверждении у фин. директора (по оплате)",
            DealDetailStatus.payment_process: "В процессе оплаты",
            DealDetailStatus.loading: "На погрузке",
            DealDetailStatus.in_transit: "Товар в пути",
            DealDetailStatus.waiting_outgoing_upd: "Ожидание исходящей УПД",
            DealDetailStatus.unloading_control: "Контроль разгрузки",
            DealDetailStatus.docs_check: "Проверка документов",
            DealDetailStatus.waiting_full_payment: "Ожидание полной оплаты",
            DealDetailStatus.closed: "Сделка закрыта",
        }
        return labels[self]


class ApplicationStatus(Enum):
    """
    Статус заявки
    """

    active = "active"
    archived = "archived"
    in_deal = "in_deal"

    def label(self):
        labels = {
            ApplicationStatus.active: "Активна",
            ApplicationStatus.archived: "В архиве",
            ApplicationStatus.in_deal: "В сделке",
        }
        return labels[self]
