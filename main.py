import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS: dict[str, Any] = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

KEYS = set(DEFAULTS)
INT_KEYS = {"port", "workers"}
BOOL_KEYS = {"debug"}

app = FastAPI(title="Effective Config API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def coerce(key: str, value: Any) -> Any:
    if key in INT_KEYS:
        return int(value)
    if key in BOOL_KEYS:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"true", "1", "yes", "on"}
    return str(value)


def normalize_layer(layer: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for key, value in layer.items():
        key = str(key).lower()
        if key in KEYS and value is not None:
            normalized[key] = coerce(key, value)
    return normalized


def read_yaml_layer() -> dict[str, Any]:
    path = BASE_DIR / "config.development.yaml"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return normalize_layer(data)


def read_dotenv_layer() -> dict[str, Any]:
    values = dotenv_values(BASE_DIR / ".env")
    layer: dict[str, Any] = {}
    for env_key, value in values.items():
        if value is None:
            continue
        if env_key == "NUM_WORKERS":
            layer["workers"] = value
        elif env_key.startswith("APP_"):
            key = env_key[4:].lower()
            if key in KEYS:
                layer[key] = value
    return normalize_layer(layer)


def read_os_layer() -> dict[str, Any]:
    layer: dict[str, Any] = {}
    for env_key, value in os.environ.items():
        if env_key.startswith("APP_"):
            key = env_key[4:].lower()
            if key in KEYS:
                layer[key] = value
    return normalize_layer(layer)


def effective_config(overrides: list[str]) -> dict[str, Any]:
    config = dict(DEFAULTS)
    # Precedence from low to high: defaults -> YAML -> .env -> OS env -> CLI query.
    config.update(read_yaml_layer())
    config.update(read_dotenv_layer())
    config.update(read_os_layer())

    for item in overrides:
        key, separator, value = item.partition("=")
        key = key.strip().lower()
        if separator and key in KEYS:
            try:
                config[key] = coerce(key, value)
            except (TypeError, ValueError):
                # Ignore invalid override values rather than returning a wrong type.
                continue

    # Never expose the actual API key in the response.
    config["api_key"] = "****"
    return config


@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    return effective_config(set)


@app.get("/")
def root():
    return {"status": "ok", "endpoint": "/effective-config"}
