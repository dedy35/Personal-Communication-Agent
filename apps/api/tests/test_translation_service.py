from app.schemas.translation import TranslationContext
from app.services.translation_service import TranslationService


def test_detect_language_japanese() -> None:
    service = TranslationService()
    assert service.detect_language("本日中に確認してご報告いただけますか。") == "ja"


def test_translate_to_indonesian_japanese_phrase() -> None:
    service = TranslationService()
    result = service.translate_to_indonesian("納期は明日までに確定できますでしょうか。")
    assert "tenggat" in result.lower() or "besok" in result.lower()


def test_explain_practical_meaning_japanese_confirm() -> None:
    service = TranslationService()
    meaning = service.explain_practical_meaning("確認お願いします")
    assert "memeriksa" in meaning.lower() or "update" in meaning.lower()


def test_analyze_tone_polite_formal() -> None:
    service = TranslationService()
    tone = service.analyze_tone("本日中に確認してご報告いただけますか。")
    assert tone in {"polite_formal", "urgent"}


def test_analyze_hierarchy_with_context() -> None:
    service = TranslationService()
    hierarchy = service.analyze_hierarchy(
        "確認お願いします",
        context=TranslationContext(relationship_type="senior", platform_name="line"),
    )
    assert hierarchy == "upward_or_external_formal"


def test_classify_urgency_high() -> None:
    service = TranslationService()
    urgency = service.classify_urgency("至急ご確認ください。")
    assert urgency == "high"


def test_explain_risk_sensitive_topic() -> None:
    service = TranslationService()
    risk = service.explain_risk(
        "今の会社に内緒で週15時間なら手伝える？",
        tone="urgent",
        hierarchy="peer_professional",
        urgency="high",
        context=TranslationContext(platform_name="line"),
    )
    assert "sensitif" in risk.lower() or "konflik" in risk.lower() or "risiko" in risk.lower()


def test_analyze_message_japanese_end_to_end() -> None:
    service = TranslationService()
    analysis = service.analyze_message(
        "本日中に確認してご報告いただけますか。",
        context=TranslationContext(relationship_type="senior", platform_name="slack"),
    )

    assert analysis.detected_language == "ja"
    assert analysis.body_original.startswith("本日中")
    assert len(analysis.body_translated) > 0
    assert analysis.urgency in {"high", "medium"}
    assert analysis.hierarchy == "upward_or_external_formal"
    assert len(analysis.risk_explanation) > 0
