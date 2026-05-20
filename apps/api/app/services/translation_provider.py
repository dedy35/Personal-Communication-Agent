from __future__ import annotations

import re
from typing import Protocol

from app.schemas.translation import TranslationContext


class TranslationProvider(Protocol):
    def detect_language(self, text: str) -> str: ...

    def translate_to_indonesian(self, text: str) -> str: ...

    def explain_practical_meaning(self, text: str, *, context: TranslationContext | None = None) -> str: ...

    def analyze_tone(self, text: str) -> str: ...

    def analyze_hierarchy(self, text: str, *, context: TranslationContext | None = None) -> str: ...

    def classify_urgency(self, text: str) -> str: ...

    def explain_risk(
        self,
        text: str,
        *,
        tone: str,
        hierarchy: str,
        urgency: str,
        context: TranslationContext | None = None,
    ) -> str: ...


class RuleBasedTranslationProvider:
    """Core mock/rule-based provider.

    This is intentionally deterministic for early-stage production reliability
    and straightforward testability. A model-based provider (Ollama/OpenAI)
    can implement the same TranslationProvider interface later.
    """

    _JP_TO_ID_RULES: list[tuple[str, str]] = [
        ("本日中に確認してご報告いただけますか。", "Bisakah Anda cek dan melaporkan hari ini?"),
        ("確認お願いします", "Mohon konfirmasi/cek."),
        ("確認してご報告いたします。", "Saya akan cek lalu melaporkan."),
        ("納期は明日までに確定できますでしょうか。", "Apakah tenggat bisa dipastikan paling lambat besok?"),
        ("返信が遅くなり申し訳ありません。", "Maaf balasan saya terlambat."),
        ("至急", "Segera / mendesak"),
    ]

    _INDONESIAN_HINTS = (
        "yang",
        "dan",
        "tidak",
        "mohon",
        "hari",
        "besok",
        "balas",
        "tolong",
    )

    _ENGLISH_HINTS = (
        "please",
        "today",
        "tomorrow",
        "urgent",
        "confirm",
        "reply",
        "thanks",
    )

    def detect_language(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return "unknown"

        if self._contains_japanese_chars(normalized):
            return "ja"

        lowered = normalized.lower()
        if any(token in lowered for token in self._INDONESIAN_HINTS):
            return "id"
        if any(token in lowered for token in self._ENGLISH_HINTS):
            return "en"
        return "unknown"

    def translate_to_indonesian(self, text: str) -> str:
        normalized = text.strip()
        if not normalized:
            return ""

        language = self.detect_language(normalized)
        if language == "id":
            return normalized

        for source, target in self._JP_TO_ID_RULES:
            if source in normalized:
                return target

        if language == "ja":
            return (
                "Terjemahan Indonesia (rule-based): pesan Jepang ini meminta klarifikasi/aksi. "
                "Gunakan analisis konteks sebelum mengirim balasan."
            )

        if language == "en":
            return f"Terjemahan Indonesia: {normalized}"

        return "Terjemahan belum tersedia untuk bahasa ini."

    def explain_practical_meaning(self, text: str, *, context: TranslationContext | None = None) -> str:
        lowered = text.lower()
        if "確認" in text or "confirm" in lowered:
            return "Pengirim meminta kamu memeriksa sesuatu dan memberi update balik."
        if "納期" in text or "deadline" in lowered:
            return "Pengirim meminta kepastian tenggat, jadi balasan cepat diperlukan."
        if "返信" in text or "reply" in lowered:
            return "Pengirim menyoroti waktu balasan dan ekspektasi respons yang tepat waktu."

        if context and context.relationship_type in {"senior", "client"}:
            return "Dalam konteks kerja formal, balasan singkat-sopan dengan next action lebih aman."

        return "Makna praktis: ada kebutuhan klarifikasi/aksi lanjutan dari pihak pengirim."

    def analyze_tone(self, text: str) -> str:
        lowered = text.lower()
        if "至急" in text or "urgent" in lowered:
            return "urgent"
        if "申し訳" in text or "maaf" in lowered:
            return "apologetic"
        if any(token in text for token in ["でしょうか", "いただけますか", "お願いします"]):
            return "polite_formal"
        if "!" in text:
            return "strong"
        return "neutral"

    def analyze_hierarchy(self, text: str, *, context: TranslationContext | None = None) -> str:
        _ = text
        if context and context.relationship_type:
            if context.relationship_type in {"senior", "client", "manager"}:
                return "upward_or_external_formal"
            if context.relationship_type in {"peer", "colleague"}:
                return "peer_professional"
            if context.relationship_type in {"friend", "family"}:
                return "casual_personal"

        return "unknown_hierarchy"

    def classify_urgency(self, text: str) -> str:
        lowered = text.lower()
        if "至急" in text or "urgent" in lowered or "asap" in lowered:
            return "high"
        if "本日中" in text or "today" in lowered:
            return "high"
        if "明日" in text or "tomorrow" in lowered:
            return "medium"
        if "FYI" in text or "fyi" in lowered:
            return "low"
        return "medium"

    def explain_risk(
        self,
        text: str,
        *,
        tone: str,
        hierarchy: str,
        urgency: str,
        context: TranslationContext | None = None,
    ) -> str:
        flags: list[str] = []
        lowered = text.lower()

        if hierarchy == "upward_or_external_formal":
            flags.append("balasan harus menjaga formalitas karena relasi senior/client")
        if tone in {"urgent", "strong"}:
            flags.append("nada pesan menekan; risiko salah prioritas jika balasan terlambat")
        if urgency == "high":
            flags.append("perlu respons cepat dengan komitmen tindakan yang jelas")
        if any(token in lowered for token in ["freelance", "retainer", "kontrak"]) or "内緒" in text:
            flags.append("mengandung topik sensitif terkait konflik kerja/kerahasiaan")

        if context and context.platform_name == "line":
            flags.append("komunikasi lintas bahasa di LINE berisiko salah nuansa, cek terjemahan dua arah")

        if not flags:
            return "Risiko rendah-menengah: tetap verifikasi target dan nada sebelum approval." 

        return "Risiko: " + "; ".join(flags) + "."

    @staticmethod
    def _contains_japanese_chars(text: str) -> bool:
        return re.search(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", text) is not None
