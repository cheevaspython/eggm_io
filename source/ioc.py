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
from source.api.agents.edit_deal.service_abc import EditDealAgentServiceAbc
from source.api.agents.reminder.service_abc import ReminderAgentServiceAbc
from source.api.agents.supervisor.service_abc import SupervisorServiceAbc
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
    providers.append(GraphProvider())

    container = make_async_container(
        *providers,
        context={Settings: settings},
    )
    return container
