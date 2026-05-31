# 🤖 JARVIS AI Chatbot

Assistente desktop com interface moderna, suporte a múltiplos provedores de IA e modo automático com ferramentas.

## Funcionalidades

- **Provedores ilimitados**: OpenAI, Anthropic (Claude), Google Gemini, Ollama (local), OpenRouter + **qualquer API compatível com OpenAI** (DeepSeek, Mistral, Groq, Together AI, Perplexity, xAI/Grok, etc.)
- **Streaming em tempo real**: Respostas aparecem caractere por caractere
- **Modo Auto**: JARVIS pode executar ferramentas (arquivos, comandos, web, sistema)
- **Histórico SQLite**: Busca rápida com FTS5, exportação (txt, md, json, pdf)
- **9 temas visuais**: Jarvis Dark/Light, Nord, Dracula, Matrix, Cyberpunk, Solarized, Tokyo Night, Catppuccin
- **Auto-tema Windows**: Segue o tema claro/escuro do sistema
- **TTS**: Leitura em voz alta das respostas
- **Plugins customizados**: Extensível via JSON
- **API keys criptografadas**: Armazenamento seguro com Fernet + PBKDF2

## Requisitos

- Python 3.10+
- Windows (usa pywin32, winsound, winreg)

## Instalação

```bash
git clone https://github.com/anomalyco/jarvis-chatbot
cd jarvis-chatbot
pip install -r requirements.txt
python main.py
```

Ou use `start.bat` ou `start.ps1`.

## Atalhos

| Atalho | Ação |
|--------|------|
| `Ctrl+N` | Nova conversa |
| `Ctrl+W` | Deletar conversa |
| `Ctrl+E` | Exportar conversa |
| `Ctrl+T` | Toggle TTS |
| `Ctrl+L` | Limpar chat |
| `Ctrl+M` | Minimizar para bandeja |
| `Ctrl+,` | Abrir configurações |
| `Enter` | Enviar mensagem |
| `Shift+Enter` | Nova linha |

## Esteira de testes

```bash
python -m pytest tests/ -v
```

## Estrutura

```
jarvis-chatbot/
├── main.py                 # Ponto de entrada
├── core/                   # Núcleo
│   ├── ai_manager.py       # Gerenciador de provedores
│   ├── conversation.py     # Gerenciador de conversas (SQLite + FTS5)
│   ├── plugin_manager.py   # Plugins customizados
│   ├── secure_config.py    # Criptografia de API keys
│   ├── logging_setup.py    # Configuração de logging
│   └── providers/          # Provedores de IA
├── agents/                 # Agentes
│   ├── base_agent.py       # Classe base
│   ├── chat_agent.py       # Modo chat
│   ├── auto_agent.py       # Modo automático
│   └── tools/              # Ferramentas
├── ui/                     # Interface gráfica
│   ├── app.py              # Janela principal
│   ├── theme_manager.py    # Gerenciador de temas
│   └── components/         # Widgets
│       ├── chat_display.py
│       ├── input_area.py
│       ├── sidebar.py
│       └── settings_window.py
├── data/                   # Dados locais
│   ├── config.json         # Config (keys criptografadas)
│   ├── conversations.db    # Histórico SQLite
│   └── plugins/            # Plugins .json
├── tests/                  # Testes
└── requirements.txt        # Dependências
```

## Licença

MIT
