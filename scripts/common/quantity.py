import re
import unicodedata

VARIANT_WORDS = (
    "選べる", "選べ", "選択", "各種", "よりどり", "アソート",
    "組み合わせ自由", "自由に選"
)


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
    if any(word in text for word in VARIANT_WORDS):
        return True
    # A single page offering "単品 / 4個セット" is not one uniquely defined comparison item.
    if "単品" in text and re.search(r"\d{1,3}\s*(?:袋|個|パック|箱|ケース)?\s*セット", text):
        return True
    return False


def _distinct_numbers(values):
    return sorted(set(round(float(v), 6) for v in values))


def _pack_counts(text: str):
    return [
        int(m.group(1))
        for m in re.finditer(r"(?<!\d)(\d{1,3})\s*(?:袋|個|パック|箱|ケース)", text)
        if 1 <= int(m.group(1)) <= 999
    ]


def _has_multiple_pack_options(text: str) -> bool:
    return len(set(_pack_counts(text))) > 1


def parse_count(title: str):
    """Return total sheet/item count only when one defensible quantity can be identified."""
    text = normalize_text(title)
    if _reject_variant(text) or _has_multiple_pack_options(text):
        return None

    explicit_patterns = [
        r"(?<!\d)(\d{1,5})\s*枚(?:入|入り)?\s*x\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)?",
        r"(?<!\d)(\d{1,5})\s*枚\s*(?:入|入り)?\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)",
    ]
    explicit_matches = []
    for pattern in explicit_patterns:
        for m in re.finditer(pattern, text):
            each, packs = int(m.group(1)), int(m.group(2))
            total = each * packs
            if 1 <= total <= 100000:
                explicit_matches.append((float(total), m.group(0)))

    explicit_totals = _distinct_numbers(x[0] for x in explicit_matches)
    if len(explicit_totals) > 1:
        return None

    singles = list(re.finditer(r"(?<!\d)(\d{1,5})\s*枚(?:入|入り)?", text))
    single_values = [int(m.group(1)) for m in singles if 1 <= int(m.group(1)) <= 100000]
    distinct_singles = sorted(set(single_values))

    if explicit_matches:
        total = explicit_totals[0]
        if len(distinct_singles) > 1 and int(total) not in distinct_singles:
            return None
        evidence = next(e for value, e in explicit_matches if round(value, 6) == total)
        return {"quantity": float(total), "confidence": 0.99, "evidence": evidence}

    # "100枚 ... 4袋" does not prove whether 100 is per bag or the case total.
    # Prefer exclusion to silently treating a case as one bag.
    if _pack_counts(text):
        return None

    if not distinct_singles or len(distinct_singles) > 1:
        return None
    return {"quantity": float(distinct_singles[0]), "confidence": 0.90, "evidence": singles[0].group(0)}


def parse_liters(title: str):
    """Return total liters. kg-only and selectable/range capacities are intentionally unsupported."""
    text = normalize_text(title)
    if _reject_variant(text) or _has_multiple_pack_options(text):
        return None

    if re.search(r"\d+(?:\.\d+)?\s*(?:~|〜|～|-|ー)\s*\d+(?:\.\d+)?\s*l", text):
        return None

    explicit_patterns = [
        r"(?<!\d)(\d+(?:\.\d+)?)\s*l(?:iter|リットル)?\s*x\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)?",
        r"(?<!\d)(\d+(?:\.\d+)?)\s*l(?:iter|リットル)?\s*(\d{1,3})\s*(?:袋|個|パック|箱|セット|ケース)",
    ]
    explicit_matches = []
    for pattern in explicit_patterns:
        for m in re.finditer(pattern, text):
            amount, packs = float(m.group(1)), int(m.group(2))
            total = amount * packs
            if 0 < total <= 1000:
                explicit_matches.append((float(total), m.group(0), amount))

    explicit_totals = _distinct_numbers(x[0] for x in explicit_matches)
    if len(explicit_totals) > 1:
        return None

    matches = list(re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*l(?:iter|リットル)?", text))
    values = [float(m.group(1)) for m in matches if 0 < float(m.group(1)) <= 1000]
    distinct_values = _distinct_numbers(values)

    if explicit_matches:
        total = explicit_totals[0]
        if len(distinct_values) > 1 and round(total, 6) not in distinct_values:
            return None
        evidence = next(e for value, e, _ in explicit_matches if round(value, 6) == total)
        return {"quantity": float(total), "confidence": 0.99, "evidence": evidence}

    if not distinct_values or len(distinct_values) > 1:
        return None
    return {"quantity": float(distinct_values[0]), "confidence": 0.90, "evidence": matches[0].group(0)}


def parse_100g(title: str):
    """Reusable future parser for dry/wet food. Not used by MVP categories yet."""
    text = normalize_text(title)
    if _reject_variant(text) or _has_multiple_pack_options(text):
        return None

    explicit_matches = list(
        re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*(kg|g)\s*x\s*(\d{1,3})", text)
    )
    totals = []
    for m in explicit_matches:
        amount = float(m.group(1))
        grams = amount * (1000 if m.group(2) == "kg" else 1) * int(m.group(3))
        if grams > 0:
            totals.append((grams, m.group(0)))
    distinct_totals = _distinct_numbers(x[0] for x in totals)
    if len(distinct_totals) > 1:
        return None
    if totals:
        grams = distinct_totals[0]
        evidence = next(e for value, e in totals if round(value, 6) == grams)
        return {"quantity": grams / 100, "confidence": 0.99, "evidence": evidence}

    matches = list(re.finditer(r"(?<!\d)(\d+(?:\.\d+)?)\s*(kg|g)", text))
    grams = []
    for m in matches:
        amount = float(m.group(1)) * (1000 if m.group(2) == "kg" else 1)
        if 1 <= amount <= 100000:
            grams.append(amount)
    distinct = _distinct_numbers(grams)
    if len(distinct) != 1:
        return None
    return {"quantity": distinct[0] / 100, "confidence": 0.90, "evidence": matches[0].group(0)}
