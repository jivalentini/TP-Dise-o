from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Servidor de base de datos
    database_url: str = "postgresql+psycopg://tp_user:tp_pass@localhost:5432/tp_evaluaciones"

    # Sesión
    jwt_secret: str = "cambiar-esto-en-produccion"
    jwt_expire_minutes: int = 60

    # Servidor LDAP de la organización
    auth_mode: str = "mock"  # "mock" | "ldap"
    mock_users: str = "CONSULTOR:consultor123"  # USUARIO:clave,USUARIO2:clave2
    ldap_server: str = "ldap://localhost:389"  # ldaps://host:636 en producción
    ldap_user_dn_template: str = "uid={username},ou=people,dc=capitalhumano,dc=com"

    # Sistemas externos
    ia_mode: str = "mock"  # "mock" | "api" (REST propio en ia_base_url) | "anthropic"
    ia_base_url: str = ""
    ia_api_key: str = ""
    ia_model: str = "claude-sonnet-4-5"
    sistema_candidatos_url: str = ""
    sistema_candidatos_api_key: str = ""
    impresora_uri: str = ""  # nombre de la cola CUPS/IPP; vacío = imprime el navegador

    # CU032 – Proceso batch de finalización de cuestionarios
    batch_intervalo_minutos: int = 60  # 0 = desactivado (se puede correr con: python -m app.batch)


settings = Settings()
