"""Shared, deliberately small language-code policy for voice and text intake."""

from typing import Optional


# Standard language codes for English and the Indic languages the provider
# boundary may receive. This is a validation policy, not a claim that every provider has
# identical recognition or localization quality for every listed language.
SUPPORTED_LANGUAGE_CODES = frozenset({
    "as", "bn", "brx", "doi", "en", "gu", "hi", "kn", "kok", "ks", "mai",
    "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur",
})
UNKNOWN_LANGUAGE = "unknown"


def normalize_language_code(value: str, *, allow_unknown: bool = False) -> str:
    """Return a supported lower-case language code or fail explicitly.

    Regional tags are intentionally not silently collapsed: callers must send
    the documented code, which avoids claiming a translation/detection choice
    the service did not make.
    """
    if not isinstance(value, str):
        raise ValueError("language code must be a string")
    code = value.strip().casefold()
    if allow_unknown and code == UNKNOWN_LANGUAGE:
        return code
    if code not in SUPPORTED_LANGUAGE_CODES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGE_CODES))
        raise ValueError(f"unsupported language code '{value}'; supported codes: {supported}")
    return code


def normalize_detected_language(value: Optional[str]) -> str:
    """Map unusable provider detection metadata to explicit UNKNOWN."""
    if value is None:
        return UNKNOWN_LANGUAGE
    try:
        return normalize_language_code(value, allow_unknown=True)
    except ValueError:
        return UNKNOWN_LANGUAGE
