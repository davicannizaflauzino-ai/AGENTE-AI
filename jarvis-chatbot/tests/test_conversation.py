"""Testes para o gerenciador de conversas."""

import os
import sys
import tempfile
import unittest

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _here)

from core.conversation import ConversationManager


class TestConversationManager(unittest.TestCase):
    def setUp(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self._orig_db = __import__("core.conversation").conversation.DB_PATH
        import core.conversation as conv
        conv.DB_PATH = self.db_path
        self.manager = ConversationManager()

    def tearDown(self):
        self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_new_conversation(self):
        cid = self.manager.new_conversation("openai", "gpt-4")
        self.assertIsNotNone(cid)
        self.assertEqual(self.manager.current_title, "Nova Conversa")

    def test_add_and_get_messages(self):
        cid = self.manager.new_conversation()
        self.manager.add_message("user", "Olá", cid)
        self.manager.add_message("assistant", "Olá! Como posso ajudar?", cid)
        msgs = self.manager.get_messages(cid)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["role"], "user")
        self.assertEqual(msgs[0]["content"], "Olá")

    def test_auto_title_from_first_message(self):
        cid = self.manager.new_conversation()
        self.manager.add_message("user", "Qual a capital do Brasil?", cid)
        convs = self.manager.get_conversations()
        self.assertIn("capital do Brasil", convs[0]["title"])

    def test_delete_conversation(self):
        cid = self.manager.new_conversation()
        self.manager.add_message("user", "teste", cid)
        self.manager.delete_conversation(cid)
        convs = self.manager.get_conversations()
        self.assertEqual(len(convs), 0)

    def test_rename_conversation(self):
        cid = self.manager.new_conversation()
        self.manager.rename_conversation(cid, "Novo Título")
        convs = self.manager.get_conversations()
        self.assertEqual(convs[0]["title"], "Novo Título")

    def test_export_json(self):
        cid = self.manager.new_conversation()
        self.manager.add_message("user", "teste", cid)
        path = tempfile.mktemp(suffix=".json")
        self.manager.export_conversation(cid, path, "json")
        with open(path, "r") as f:
            import json
            data = json.load(f)
        self.assertIn("messages", data)
        os.unlink(path)

    def test_export_md(self):
        cid = self.manager.new_conversation()
        self.manager.add_message("user", "teste", cid)
        path = tempfile.mktemp(suffix=".md")
        self.manager.export_conversation(cid, path, "md")
        with open(path, "r") as f:
            content = f.read()
        self.assertIn("teste", content)
        os.unlink(path)


if __name__ == "__main__":
    unittest.main()