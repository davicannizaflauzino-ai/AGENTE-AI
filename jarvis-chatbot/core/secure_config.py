import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")

try:
    import win32cred
    _HAS_WIN32CRED = True
except ImportError:
    _HAS_WIN32CRED = False

_CRED_TARGET_PREFIX = "JarvisAI_apikey_"


def _cred_target(provider_key: str) -> str:
    return f"{_CRED_TARGET_PREFIX}{provider_key}"


def _store_cred(target: str, value: str) -> bool:
    if not _HAS_WIN32CRED or not value:
        return False
    try:
        import win32con
        cred = {
            "Type": win32con.CRED_TYPE_GENERIC,
            "TargetName": target,
            "CredentialBlob": value,
            "Persist": win32con.CRED_PERSIST_LOCAL_MACHINE,
            "UserName": "jarvis",
        }
        win32cred.CredWrite(cred, 0)
        return True
    except Exception as e:
        logger.warning("Falha ao salvar credencial no Windows Credential Manager: %s", e)
        return False


def _read_cred(target: str) -> Optional[str]:
    if not _HAS_WIN32CRED:
        return None
    try:
        cred = win32cred.CredRead(target, 1)  # CRED_TYPE_GENERIC = 1
        blob = cred.get("CredentialBlob", b"")
        if isinstance(blob, bytes):
            return blob.decode("utf-8").rstrip("\x00")
        return str(blob).rstrip("\x00")
    except Exception:
        return None


def _delete_cred(target: str) -> None:
    if not _HAS_WIN32CRED:
        return
    try:
        win32cred.CredDelete(target, 1)
    except Exception:
        pass


def store_api_key(provider_key: str, api_key: str) -> bool:
    return _store_cred(_cred_target(provider_key), api_key)


def read_api_key(provider_key: str) -> Optional[str]:
    return _read_cred(_cred_target(provider_key))


def delete_api_key(provider_key: str) -> None:
    _delete_cred(_cred_target(provider_key))


def dump_config(data: dict):
    os.makedirs(_CONFIG_DIR, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config() -> dict:
    if not os.path.exists(_CONFIG_PATH):
        return {}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def encrypt_config_providers(providers: dict) -> dict:
    encrypted = {}
    for key, cfg in providers.items():
        entry = dict(cfg)
        api_key = entry.pop("api_key", None)
        if api_key:
            store_api_key(key, api_key)
            entry["_has_key"] = True
        encrypted[key] = entry
    return encrypted


def decrypt_config_providers(providers: dict) -> dict:
    decrypted = {}
    for key, cfg in providers.items():
        entry = dict(cfg)
        if entry.pop("_has_key", False):
            stored = read_api_key(key)
            entry["api_key"] = stored or ""
        else:
            entry.setdefault("api_key", "")
        decrypted[key] = entry
    return decrypted


def clear_stored_api_keys(providers: dict):
    for key in providers:
        delete_api_key(key)
