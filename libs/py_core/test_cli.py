import asyncio

from chatlib.global_config import GlobalConfig
from chatlib.llm.integration.openai_api import GPTChatCompletionAPI
from py_core import ModeratorSession
from py_core.cli import test_session_loop
from py_core.system.storage.session.json import JsonSessionStorage
from py_core.utils.deepl_translator import DeepLTranslator

GlobalConfig.is_cli_mode = True
GPTChatCompletionAPI.assert_authorize()
DeepLTranslator.assert_authorize()

session = ModeratorSession(JsonSessionStorage())

asyncio.run(test_session_loop(session))
