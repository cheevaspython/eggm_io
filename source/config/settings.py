import os
import pytz

from pathlib import Path
from urllib.parse import quote_plus
from typing import Optional, Tuple

from pydantic import BaseModel, Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8088
    production: bool = False


class ProjectName(BaseModel):
    title: str = "v1pn"
    path: str = ""  # TODO
    access: str = "Access to v1pn."


class DbSettings(BaseModel):
    url: str | PostgresDsn | None = None
    test_url: str | PostgresDsn | None = None
    echo: bool = False
    echo_pool: bool = False
    max_overflow: int = 50
    pool_size: int = 10
    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @staticmethod
    def _read_secret_or_env(
        secret_name: str,
        env_var_name: str,
        default: str = "TEST",
    ) -> str:
        run_secret = Path("/run/secrets") / secret_name
        if run_secret.exists() and run_secret.is_file():
            return run_secret.read_text().strip()

        # fallback на переменную окружения, затем на default
        return os.getenv(env_var_name, default)

    @classmethod
    def create_url(
        cls,
        user_secret_name: str,
        password_secret_name: str,
        db_name: Optional[str] = None,
    ) -> str:
        db = db_name or os.getenv("POSTGRES_DB", "postgres")
        user = cls._read_secret_or_env(
            user_secret_name,
            "POSTGRES_USER",
            "postgres",
        )
        password = cls._read_secret_or_env(
            password_secret_name,
            "POSTGRES_PASSWORD",
            "",
        )
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")

        return (
            f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}"
            f"@{host}:{port}/{db}"
        )

    @classmethod
    def create_test_url(
        cls,
        user_secret_name: str,
        password_secret_name: str,
    ) -> str:
        return cls.create_url(
            user_secret_name=user_secret_name,
            password_secret_name=password_secret_name,
            db_name="test_database",
        )

    def __init__(self, **kwargs):
        user_secret_name = os.getenv("PSQL_USER_SECRET_NAME", "")
        password_secret_name = os.getenv("PSQL_PASSWORD_SECRET_NAME", "")

        kwargs.setdefault(
            "url",
            type(self).create_url(
                user_secret_name=user_secret_name,
                password_secret_name=password_secret_name,
            ),
        )
        kwargs.setdefault(
            "test_url",
            type(self).create_test_url(
                user_secret_name=user_secret_name,
                password_secret_name=password_secret_name,
            ),
        )
        super().__init__(**kwargs)


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"
    auth: str = "/auth"
    pub: str = "/pub"
    admin: str = "/admin"


class JWTTokenSettings(BaseModel):
    lifetime_seconds: Optional[int] = 60480
    secret: str = "iYo1Eslz-PIqG_Q9jgl7o!Liu63Hz9M2O1FoMkwzr4k="
    internal_secret: str = "iYo1EElz-PIqg_Q9jgl7o_LiU68Hz9M2O1FoMkwZr5k="
    reset_password_token_secret: str = "test_secret_token_reset_key"
    verification_token_secret: str = "test_secret_token_verify_key"
    len: int = 43


class RoboKassaConfig(BaseModel):
    merchant_login: str = "yastvo"
    password1: str = ""
    password2: str = ""
    is_test: bool = True
    create_payment_url: str = (
        "https://services.robokassa.ru/InvoiceServiceWebApi/api/CreateInvoice"
    )
    polling_url: str = (
        "https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt"
    )
    xml_ns: str = "http://auth.robokassa.ru/Merchant/WebService/"
    # TODO refact
    opstate_url: str = (
        "https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt"
    )
    default_backoff: list[int] = [60, 60, 60, 60, 60]
    white_list: list[str] = ["185.59.216.65", "185.59.217.65", "188.94.159.36"]

    def __init__(self, **data):
        def get_secret_or_env(
            env_key: str,
            default_secret_name: str,
        ) -> str:
            """
            1) Берём имя/значение из env.
            2) Если существует файл /run/secrets/<значение>, читаем оттуда (Swarm).
            3) Иначе считаем, что это уже реальный пароль из .env (Compose/dev).
            """
            name_or_value = os.getenv(env_key, default_secret_name)
            secret_path = Path(f"/run/secrets/{name_or_value}")
            if secret_path.exists():
                return secret_path.read_text().strip()
            return name_or_value

        pw1 = get_secret_or_env("FASTAPI_CFG__ROBOKASSA__PASSWORD1", "robo_pass1")
        pw2 = get_secret_or_env("FASTAPI_CFG__ROBOKASSA__PASSWORD2", "robo_pass2")

        data.setdefault("password1", pw1)
        data.setdefault("password2", pw2)
        super().__init__(**data)


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()

    @property
    def bearer_token_url(self) -> str:
        parts = (self.prefix, self.v1.prefix, self.v1.auth, "/login")
        path = "".join(parts)
        return path.removeprefix("/")


class MediaPathSettings(BaseModel):
    upload_image: str = "media/"


class MediaTypesSettings(BaseModel):
    accessed_types: Tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "text/csv",
    )


class RedisTimeDestroySettings(BaseModel):
    destroy_sec: int = 300
    cache_ttl: int = 300


class VerifyCodeSettings(BaseModel):
    code: int = 123456
    default: bool = False


class WorkerSettings(BaseModel):
    celery_broker_url: str = ""
    cache_redis_url: str = ""
    celery_result_backend: str = ""
    result_ex_time: int = 1000

    def __init__(self, **data):
        def get_secret_or_env(
            env_key: str,
            default_secret_name: str,
        ) -> str:
            """
            1) Берём имя/значение из env.
            2) Если существует файл /run/secrets/<значение>, читаем оттуда (Swarm).
            3) Иначе считаем, что это уже реальный пароль из .env (Compose/dev).
            """
            name_or_value = os.getenv(env_key, default_secret_name)
            secret_path = Path(f"/run/secrets/{name_or_value}")
            if secret_path.exists():
                return secret_path.read_text().strip()
            return name_or_value

        redis_password = get_secret_or_env("REDIS_PASSWORD", "redis_password")

        # TODO rm hardcode
        redis_password = "redis"

        redis_url = (
            f"redis://:{redis_password}@redis:6379/0"  # TODO add redis name from env
        )
        data.setdefault("celery_broker_url", redis_url)
        data.setdefault("celery_result_backend", redis_url)
        super().__init__(**data)


class MiddlewareSettings(BaseModel):
    cors_origins: list[str] = []
    allow_methods: list[str] = ["GET", "POST", "OPTIONS"]  # TODO
    allow_headers: list[str] = ["Authorization", "Content-Type"]


class ElasticSettings(BaseModel):
    elastic_port: int = 9200
    elastic_host: str = "elasticsearch"


class TelegramSettings(BaseModel):
    bot_token: str = ""
    channel_id: int = 0
    enabled: bool = True


class OpenAiSettings(BaseModel):
    api_key: SecretStr = SecretStr("")
    model: str = "gpt-4o-mini"

    def __init__(self, **data: str | SecretStr) -> None:
        secret_path = "io_token"
        gpt_api_key = self._read_secret_or_env(
            secret_name=secret_path,
            env_var_name="GPT_KEY",
            default="",
        )
        data.setdefault("api_key", SecretStr(gpt_api_key))
        super().__init__(**data)

    @staticmethod
    def _read_secret_or_env(
        secret_name: str,
        env_var_name: str,
        default: str = "None",
    ) -> str:
        run_secret = Path("/run/secrets") / secret_name
        if run_secret.exists() and run_secret.is_file():
            return run_secret.read_text().strip()
        return os.getenv(env_var_name, default)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="FASTAPI_CFG__",
        extra="ignore",
    )
    db: DbSettings = DbSettings()
    tz: pytz.tzinfo.BaseTzInfo = pytz.timezone("Europe/Moscow")
    verify: VerifyCodeSettings = VerifyCodeSettings()
    run: RunConfig = RunConfig()
    names: ProjectName = ProjectName()
    api: ApiPrefix = ApiPrefix()
    robokassa: RoboKassaConfig = RoboKassaConfig()
    middleware: MiddlewareSettings = MiddlewareSettings()
    worker: WorkerSettings = WorkerSettings()
    jwt_token: JWTTokenSettings = JWTTokenSettings()
    redis: RedisTimeDestroySettings = RedisTimeDestroySettings()
    openai: OpenAiSettings = Field(default_factory=OpenAiSettings)
    elastic: ElasticSettings = ElasticSettings()
    tg: TelegramSettings = TelegramSettings()


settings = Settings()
