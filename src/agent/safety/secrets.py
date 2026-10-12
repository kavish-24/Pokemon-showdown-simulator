import os

from src.agent.models import SecretName


def get_secret(name: SecretName) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is not configured.")
    return value
