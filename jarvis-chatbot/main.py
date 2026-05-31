#!/usr/bin/env python3
import sys
import os
import traceback

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
os.chdir(_here)

from core.logging_setup import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)


def main():
    try:
        from ui.app import JarvisApp
        logger.info("Iniciando JARVIS AI Chatbot")
        app = JarvisApp()
        app.run()
    except Exception as e:
        error_msg = f"Erro ao iniciar JARVIS:\n\n{e}\n\n{traceback.format_exc()}"
        logger.critical("Falha na inicialização: %s", error_msg)
        print(error_msg)
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("Erro", error_msg)
        except Exception:
            input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()