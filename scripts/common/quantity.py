import re
import unicodedata

VARIANT_WORDS = ("選べる", "選択", "各種", "よりどり", "アソート")


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return (
        text.replace("Ｘ", "x")
        .replace("×", "x")
        .replace("✕", "x")
        .replace("*", "x")
        .replace(",", "")
        .lower()
    )


def _reject_variant(text: str) -> bool:
    return any(word in text for word in VARIANT_WORDS)


def parse_count(title: str):
    """Return total sheet/item count only when the title has a defensible quantity."""
    text = normalize_text(title)
    if _reject_variant(text):
        return None

    explicit_patterns = [
        r"(?<!\d)(\d{1,5})\s*枚(?:入|入り)?\s*x\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)?",
        r"(?<!\d)(\d{1,5})\s*枚\s*(?:入|入り)?\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)",
    ]
    for pattern in explicit_patterns:
        m = re.search(pattern, text)
        if m:
            each, packs = int(m.group(1)), int(m.group(2))
            total = each * packs
            if 1 <= total <= 100000:
                return {"quantity": float(total), "confidence": 0.99, "evidence": m.group(0)}

    singles = list(re.finditer(r"(?<!\d)(\d{1,5})\s*枚(?:入|入り)?", text))
    values = [int(m.group(1)) for m in singles if 1 <= int(m.group(1)) <= 100000]
    if not values:
        return None

    distinct = sorted(set(values))
    if len(distinct) > 1:
        return None
    return {"quantity": float(distinct[0]), "confidence": 0.90, "evidence": singles[0].group(0)}


def parse_liters(title: str):
    """Return total liters. kg-only titles are intentionally unsupported."""
    text = normalize_text(title)
    if _reject_variant(text):
        return None

    explicit = re.search(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*l(?:iter|リットル)?\s*x\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)?",
        text,
    )
    if explicit:
        amount, packs = float(explicit.group(1)), int(explicit.group(2))
        total = amount * packs
        if 0 < total <= 1000:
            return {"quantity": total, "confidence": 0.99, "evidence": explicit.group(0)}

    compound = re.search(
        r"(?<!\d)(\d+(?:\.\d+)?)\s*l(?:iter|リットル)?\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)",
        text,
    )
    if compound:
        amount, packs = float(compound.group(1)), int(compound.group(2))
        total = amount * packs
        if 0 < total <= 1000:
            return {"quantity": total, "confidence": 0.97, "evidence": compound.group(0)}

    matches = list(re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*l(?:iter|リットル)?", text))
    values = [float(m.group(1)) for m in matches if 0 < float(m.group(1)) <= 1000]
    if not values:
        return None
    distinct = sorted(set(values))
    if len(distinct) > 1:
        return None
    return {"quantity": distinct[0], "confidence": 0.90, "evidence": matches[0].group(0)}


def parse_100g(title: str):
    """Reusable future parser for dry/wet food. Not used by MVP categories yet."""
    text = normalize_text(title)
    if _reject_variant(text):
        return None

    explicit = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*(kg|g)\s*x\s*(\d{1,3})", text)
    if explicit:
        amount = float(explicit.group(1))
        unit = explicit.group(2)
        packs = int(explicit.group(3))
        grams = amount * (1000 if unit == "kg" else 1) * packs
        if grams > 0:
            return {"quantity": grams / 100, "confidence": 0.99, "evidence": explicit.group(0)}

    matches = list(re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*(kg|g)", text))
    grams = []
    for m in matches:
        amount = float(m.group(1)) * (1000 if m.group(2) == "kg" else 1)
        if 1 <= amount <= 100000:
            grams.append(amount)
    distinct = sorted(set(grams))
    if len(distinct) != 1:
        return None
    return {"quantity": distinct[0] / 100, "confidence": 0.90, "evidence": matches[0].group(0)}
