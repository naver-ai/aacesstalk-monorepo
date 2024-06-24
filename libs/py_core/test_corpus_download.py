import asyncio

from py_core.utils.tts.clova_voice import ClovaVoice, ClovaVoiceParams
from chatlib.global_config import GlobalConfig
from py_core.utils.aac_corpus_downloader import AACCorpusDownloader

GlobalConfig.is_cli_mode = True

AACCorpusDownloader.assert_authorize()

AACCorpusDownloader.download_corpus_cli()