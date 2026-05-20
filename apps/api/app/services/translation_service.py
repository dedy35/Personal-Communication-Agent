from __future__ import annotations

from app.schemas.translation import TranslationAnalysis, TranslationContext
from app.services.translation_provider import RuleBasedTranslationProvider, TranslationProvider


class TranslationService:
    """Core translation and nuance service.

    Translation is a primary capability in this product, so this service is
    designed as a stable core API. Provider can later be swapped with
    Ollama/OpenAI while keeping this interface unchanged.
    """

    def __init__(self, provider: TranslationProvider | None = None) -> None:
        self._provider = provider or RuleBasedTranslationProvider()

    def detect_language(self, text: str) -> str:
        return self._provider.detect_language(text)

    def translate_to_indonesian(self, text: str) -> str:
        return self._provider.translate_to_indonesian(text)

    def explain_practical_meaning(self, text: str, *, context: TranslationContext | None = None) -> str:
        return self._provider.explain_practical_meaning(text, context=context)

    def analyze_tone(self, text: str) -> str:
        return self._provider.analyze_tone(text)

    def analyze_hierarchy(self, text: str, *, context: TranslationContext | None = None) -> str:
        return self._provider.analyze_hierarchy(text, context=context)

    def classify_urgency(self, text: str) -> str:
        return self._provider.classify_urgency(text)

    def explain_risk(
        self,
        text: str,
        *,
        tone: str,
        hierarchy: str,
        urgency: str,
        context: TranslationContext | None = None,
    ) -> str:
        return self._provider.explain_risk(
            text,
            tone=tone,
            hierarchy=hierarchy,
            urgency=urgency,
            context=context,
        )

    def analyze_message(self, text: str, *, context: TranslationContext | None = None) -> TranslationAnalysis:
        detected_language = self.detect_language(text)
        body_translated = self.translate_to_indonesian(text)
        practical_meaning = self.explain_practical_meaning(text, context=context)
        tone = self.analyze_tone(text)
        hierarchy = self.analyze_hierarchy(text, context=context)
        urgency = self.classify_urgency(text)
        risk_explanation = self.explain_risk(
            text,
            tone=tone,
            hierarchy=hierarchy,
            urgency=urgency,
            context=context,
        )

        return TranslationAnalysis(
            detected_language=detected_language,
            body_original=text,
            body_translated=body_translated,
            practical_meaning=practical_meaning,
            tone=tone,
            hierarchy=hierarchy,
            urgency=urgency,
            risk_explanation=risk_explanation,
        )
