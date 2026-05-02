"""
TTS（Text-to-Speech）音声生成モジュール。
gTTS（Google Translate TTS経由・完全無料）を使用。
"""

import logging
import os
import uuid
from pathlib import Path

log = logging.getLogger(__name__)

TEMP_DIR = Path("/tmp/reel_pipeline/audio")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class TTSGenerator:
    """
    音声生成。優先順位:
    1. gTTS（完全無料、インターネット必要）
    2. pyttsx3（完全オフライン、品質は低め）
    """

    def generate(self, text: str, lang: str = "ja") -> Path:
        """テキストから音声MP3を生成してパスを返す"""
        if not text.strip():
            return None

        out_path = TEMP_DIR / f"tts_{uuid.uuid4().hex[:8]}.mp3"

        try:
            return self._gtts(text, lang, out_path)
        except Exception as e:
            log.warning(f"gTTS失敗 ({e}) → pyttsx3フォールバック")
            try:
                return self._pyttsx3(text, out_path)
            except Exception as e2:
                log.error(f"TTS完全失敗: {e2}")
                return None

    def _gtts(self, text: str, lang: str, out_path: Path) -> Path:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(out_path))
        log.info(f"✓ gTTS音声生成: {out_path.name}")
        return out_path

    def _pyttsx3(self, text: str, out_path: Path) -> Path:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.save_to_file(text, str(out_path))
        engine.runAndWait()
        log.info(f"✓ pyttsx3音声生成: {out_path.name}")
        return out_path
