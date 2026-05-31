"""Testes para o módulo de configuração segura."""

import os
import sys
import unittest
from unittest.mock import patch

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _here)

from core.secure_config import (
    encrypt_config_providers,
    decrypt_config_providers,
    store_api_key,
    read_api_key,
    delete_api_key,
    dump_config,
    load_config,
)


class TestSecureConfig(unittest.TestCase):
    def test_encrypt_decrypt_config_empty(self):
        encrypted = encrypt_config_providers({})
        self.assertEqual(encrypted, {})

        decrypted = decrypt_config_providers({})
        self.assertEqual(decrypted, {})

    def test_encrypt_config_providers_api_key_stored(self):
        with patch("core.secure_config.store_api_key", return_value=True) as mock_store:
            providers = {
                "openai": {"api_key": "sk-test", "model": "gpt-4"},
            }
            encrypted = encrypt_config_providers(providers)
            mock_store.assert_called_once_with("openai", "sk-test")
            self.assertTrue(encrypted["openai"].pop("_has_key"))
            self.assertEqual(encrypted["openai"]["model"], "gpt-4")
            self.assertNotIn("api_key", encrypted["openai"])

    def test_decrypt_config_providers_api_key_retrieved(self):
        with patch("core.secure_config.read_api_key", return_value="sk-retrieved"):
            providers = {
                "openai": {"_has_key": True, "model": "gpt-4"},
            }
            decrypted = decrypt_config_providers(providers)
            self.assertEqual(decrypted["openai"]["api_key"], "sk-retrieved")
            self.assertEqual(decrypted["openai"]["model"], "gpt-4")
            self.assertNotIn("_has_key", decrypted["openai"])

    def test_decrypt_config_no_key_flag(self):
        providers = {
            "openai": {"model": "gpt-4"},
        }
        decrypted = decrypt_config_providers(providers)
        self.assertEqual(decrypted["openai"]["api_key"], "")
        self.assertEqual(decrypted["openai"]["model"], "gpt-4")

    def test_dump_load_config(self):
        data = {"test": "value", "number": 42}
        dump_config(data)
        loaded = load_config()
        self.assertEqual(loaded, data)
        dump_config({})  # cleanup

    def test_dump_load_config_corrupted(self):
        import json
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "config.json"
        )
        with open(path, "w") as f:
            f.write("{corrupted")
        loaded = load_config()
        self.assertEqual(loaded, {})


if __name__ == "__main__":
    unittest.main()
