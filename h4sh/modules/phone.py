"""Offline phone-number validation. It does not identify or locate a person."""
from __future__ import annotations

from h4sh.core.privacy import mask_phone


async def inspect(raw: str, region: str = "BR") -> dict:
    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder
    except ImportError as exc:
        raise RuntimeError("Dependência ausente: instale 'phonenumbers' com pip.") from exc
    try:
        number = phonenumbers.parse(raw.strip(), region.upper())
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"Número inválido: {exc}") from exc
    valid = phonenumbers.is_valid_number(number)
    return {
        "input_masked": mask_phone(raw),
        "valid": valid,
        "possible": phonenumbers.is_possible_number(number),
        "e164": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164) if valid else None,
        "international": phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.INTERNATIONAL) if valid else None,
        "country_code": number.country_code,
        "region": geocoder.description_for_number(number, "pt") or None,
        "carrier": carrier.name_for_number(number, "pt") or None,
        "notice": "Validação local; não identifica proprietário nem fornece localização em tempo real.",
    }
