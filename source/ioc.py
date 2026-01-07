from collections.abc import AsyncIterator
from typing import AsyncIterable, AsyncGenerator

from aiohttp import ClientSession
import redis.asyncio as aioredis
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from elasticsearch import AsyncElasticsearch
from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    make_async_container,
    from_context,
    provide,
)
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from openai import AsyncOpenAI

from dishka.integrations.taskiq import TaskiqProvider
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from taskiq import AsyncBroker

from source.config.logging import logger
from source.api.agents.confirmation.service_abc import ConfirmationAgentServiceAbc
from source.api.agents.confirmation.service_impl import ConfirmationAgentServiceImpl
from source.api.agents.edit_deal.service_abc import EditDealAgentServiceAbc
from source.api.agents.edit_deal.service_impl import EditDealAgentServiceImpl
from source.api.agents.reminder.service_abc import ReminderAgentServiceAbc
from source.api.agents.reminder.service_impl import ReminderAgentServiceImpl
from source.api.agents.supervisor.service_abc import SupervisorServiceAbc
from source.api.agents.supervisor.service_impl import SupervisorServiceImpl
from source.api.agents.interactor_abc import AgentsInteractorAbc
from source.api.agents.interactor_impl import AgentsInteractorImpl
from source.api.interfaces.deal.gateway_abc import DealGatewayAbc
from source.api.interfaces.deal.gateway_impl import DealGatewayImpl
from source.api.interfaces.application.gateway_abc import ApplicationGatewayAbc
from source.api.interfaces.application.gateway_impl import ApplicationGatewayImpl
from source.api.interfaces.deal_reminder.gateway_abc import DealReminderGatewayAbc
from source.api.interfaces.deal_reminder.gateway_impl import DealReminderGatewayImpl
from source.services.prompts.confirmation_prompts import ConfirmationAgentPrompts
from source.services.prompts.edit_deal_prompts import EditDealAgentPrompts
from source.services.prompts.reminder_prompts import ReminderAgentPrompts
from source.services.prompts.supervisor_prompts import SupervisorPrompts
from source.common.commiter import Commiter
from source.common.constrants import (
    SUPERVISOR,
    CONFIRM_AGENT,
    EDIT_DEAL_AGENT,
    REMINDER_AGENT,
)
from source.db.db_helper import db_helper
from source.db.models.choises.enum import TaskTypeChoises
from source.db.sa_commiter import SACommiter
from source.config.settings import Settings, settings
from source.errors.general import GeneralCustomError
from source.infra.telegram.client import TelegramClient
from source.schemas.pydantic.agents.state import State
from source.tasks.register import register_tasks
from source.config.task_setup import create_broker


class AppProvider(Provider):
    config = from_context(provides=Settings, scope=Scope.APP)

    # db
    sa_commiter = provide(
        SACommiter,
        scope=Scope.REQUEST,
        provides=Commiter,
    )


class BrokerProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_broker(
        self,
        config: Settings,
    ) -> AsyncIterator[AsyncBroker]:
        broker = create_broker(config=config)
        register_tasks(broker=broker)
        await broker.startup()
        try:
            yield broker
        finally:
            await broker.shutdown()


class AiohttpProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def provide_aiohttp_session(self) -> AsyncIterable[ClientSession]:
        async with ClientSession() as session:
            yield session


class TelegramProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_telegram_session(
        self,
    ) -> AsyncIterable[ClientSession]:
        async with ClientSession() as session:
            yield session

    @provide(scope=Scope.APP)
    async def provide_bot(
        self,
        config: Settings,
    ) -> AsyncIterable[Bot]:
        bot = Bot(
            token=config.tg.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
            ),
        )
        try:
            yield bot
        finally:
            await bot.session.close()

    @provide(scope=Scope.APP)
    def provide_client(
        self,
        config: Settings,
        session: ClientSession,
    ) -> TelegramClient:
        return TelegramClient(
            bot_token=config.tg.bot_token,
            chat_id=config.tg.channel_id,
            session=session,
        )


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_redis(
        self,
        config: Settings,
    ) -> aioredis.Redis:
        url = config.worker.celery_broker_url
        return aioredis.from_url(url)


class SessionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[AsyncSession,]:
        async with session_maker() as session:
            yield session

    @provide(scope=Scope.APP)
    def provide_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return db_helper.session_factory


class ElasticsearchProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_elastic(
        self,
        config: Settings,
    ) -> AsyncGenerator[AsyncElasticsearch, None]:
        if config.run.production:
            client = AsyncElasticsearch(
                hosts=[
                    f"http://main_{config.elastic.elastic_host}:{config.elastic.elastic_port}"
                ]
            )
        else:
            client = AsyncElasticsearch(
                hosts=[
                    f"http://{config.elastic.elastic_host}:{config.elastic.elastic_port}"
                ]
            )
        try:
            yield client
        finally:
            await client.close()


class OpenAIProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_openai(
        self,
        config: Settings,
    ) -> ChatOpenAI:
        try:
            return ChatOpenAI(
                api_key=config.openai.api_key,
                model=config.openai.model,
                temperature=1.2,
            )
        except Exception as e:
            raise GeneralCustomError(
                text=f"IO API KEY ERROR: {config.openai.api_key}",
                error=f"{e}",
            )

    @provide(scope=Scope.APP)
    def provide_openai_client(
        self,
        config: Settings,
    ) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=config.openai.api_key.get_secret_value())

    @provide(scope=Scope.APP)
    def provide_checkpointer(self) -> InMemorySaver:
        return InMemorySaver()


class AgentProvider(Provider):
    """
    Provider для AI-агентов и промптов.
    """

    # Промпты (синглтоны на уровне приложения)
    @provide(scope=Scope.APP)
    def provide_supervisor_prompts(self) -> SupervisorPrompts:
        return SupervisorPrompts()

    @provide(scope=Scope.APP)
    def provide_reminder_prompts(self) -> ReminderAgentPrompts:
        return ReminderAgentPrompts()

    @provide(scope=Scope.APP)
    def provide_confirmation_prompts(self) -> ConfirmationAgentPrompts:
        return ConfirmationAgentPrompts()

    @provide(scope=Scope.APP)
    def provide_edit_deal_prompts(self) -> EditDealAgentPrompts:
        return EditDealAgentPrompts()

    # Агенты (REQUEST scope для гибкости)
    @provide(scope=Scope.REQUEST, provides=SupervisorServiceAbc)
    def provide_supervisor(
        self,
        llm: ChatOpenAI,
        prompts: SupervisorPrompts,
    ) -> SupervisorServiceImpl:
        return SupervisorServiceImpl(llm=llm, supervisor_prompts=prompts)

    @provide(scope=Scope.REQUEST, provides=ReminderAgentServiceAbc)
    def provide_reminder_agent(
        self,
        llm: ChatOpenAI,
        prompts: ReminderAgentPrompts,
    ) -> ReminderAgentServiceImpl:
        return ReminderAgentServiceImpl(llm=llm, reminder_prompts=prompts)

    @provide(scope=Scope.REQUEST, provides=ConfirmationAgentServiceAbc)
    def provide_confirmation_agent(
        self,
        llm: ChatOpenAI,
        prompts: ConfirmationAgentPrompts,
    ) -> ConfirmationAgentServiceImpl:
        return ConfirmationAgentServiceImpl(llm=llm, confirmation_prompts=prompts)

    @provide(scope=Scope.REQUEST, provides=EditDealAgentServiceAbc)
    def provide_edit_deal_agent(
        self,
        llm: ChatOpenAI,
        prompts: EditDealAgentPrompts,
    ) -> EditDealAgentServiceImpl:
        return EditDealAgentServiceImpl(llm=llm, edit_deal_prompts=prompts)

    # Интерактор для оркестрации агентов
    @provide(scope=Scope.REQUEST, provides=AgentsInteractorAbc)
    def provide_agents_interactor(
        self,
        graph: CompiledStateGraph,
    ) -> AgentsInteractorImpl:
        return AgentsInteractorImpl(graph=graph)


class GraphProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=CompiledStateGraph)
    async def provide_graph(
        self,
        confirm_agent: ConfirmationAgentServiceAbc,
        edit_deal_agent: EditDealAgentServiceAbc,
        reminder_agent: ReminderAgentServiceAbc,
        supervisor_agent: SupervisorServiceAbc,
        checkpointer: InMemorySaver,
    ) -> CompiledStateGraph:
        workflow = StateGraph(State)

        workflow.add_node(SUPERVISOR, supervisor_agent)
        workflow.add_node(CONFIRM_AGENT, confirm_agent)
        workflow.add_node(EDIT_DEAL_AGENT, edit_deal_agent)
        workflow.add_node(REMINDER_AGENT, reminder_agent)

        workflow.set_entry_point(SUPERVISOR)

        def supervisor_route(state: State) -> str:
            task_type = state.task_type
            try:
                if task_type:
                    return task_type.value
                return TaskTypeChoises.reminder_agent.value
            except Exception as e:
                logger.error(f"[SUPERVISOR_ROUTE] Error determining route: {e}")
                return TaskTypeChoises.reminder_agent.value

        workflow.add_conditional_edges(
            SUPERVISOR,
            supervisor_route,
            {
                CONFIRM_AGENT: CONFIRM_AGENT,
                EDIT_DEAL_AGENT: EDIT_DEAL_AGENT,
                REMINDER_AGENT: REMINDER_AGENT,
            },
        )

        workflow.add_edge(CONFIRM_AGENT, END)
        workflow.add_edge(EDIT_DEAL_AGENT, END)
        workflow.add_edge(REMINDER_AGENT, END)

        return workflow.compile(checkpointer=checkpointer)


class GatewayProvider(Provider):
    """
    Provider для Database Gateway (репозиториев).
    """

    @provide(scope=Scope.REQUEST, provides=DealGatewayAbc)
    def provide_deal_gateway(
        self,
        session: AsyncSession,
    ) -> DealGatewayImpl:
        return DealGatewayImpl(session=session)

    @provide(scope=Scope.REQUEST, provides=ApplicationGatewayAbc)
    def provide_application_gateway(
        self,
        session: AsyncSession,
    ) -> ApplicationGatewayImpl:
        return ApplicationGatewayImpl(session=session)

    @provide(scope=Scope.REQUEST, provides=DealReminderGatewayAbc)
    def provide_deal_reminder_gateway(
        self,
        session: AsyncSession,
    ) -> DealReminderGatewayImpl:
        return DealReminderGatewayImpl(session=session)


def setup_di() -> AsyncContainer:
    providers = []
    providers.append(AppProvider())
    providers.append(TaskiqProvider())
    providers.append(BrokerProvider())
    providers.append(TelegramProvider())
    providers.append(RedisProvider())
    providers.append(SessionProvider())
    providers.append(AiohttpProvider())
    providers.append(ElasticsearchProvider())
    providers.append(OpenAIProvider())
    providers.append(AgentProvider())
    providers.append(GraphProvider())
    providers.append(GatewayProvider())

    container = make_async_container(
        *providers,
        context={Settings: settings},
    )
    return container
