from .quantity import normalize_text


def sheet_size(title: str) -> str:
    text = normalize_text(title)
    if "スーパーワイド" in text or "super wide" in text:
        return "super_wide"
    if "ワイド" in text or "wide" in text:
        return "wide"
    if "レギュラー" in text or "regular" in text:
        return "regular"
    return "unknown"


def litter_material(title: str) -> str:
    text = normalize_text(title)
    if any(k in text for k in ("システムトイレ", "デオトイレ", "ニャンとも", "サンド")):
        return "system"
    if any(k in text for k in ("ベントナイト", "鉱物")):
        return "mineral"
    if any(k in text for k in ("おから", "豆腐", "とうふ")):
        return "okara"
    if any(k in text for k in ("ひのき", "ヒノキ", "木製", "木の", "パイン", "ウッド")):
        return "wood"
    if any(k in text for k in ("シリカ", "silica")):
        return "silica"
    if any(k in text for k in ("紙製", "紙の", "ペーパー")):
        return "paper"
    return "unknown"


def compatibility(title: str) -> str:
    text = normalize_text(title)
    if "デオトイレ" in text:
        return "deotoilet"
    if "ニャンとも" in text or "にゃんとも" in text:
        return "nyantomo"
    if "アイリス" in text or "ラクリーン" in text or "tih-" in text or "s-ss" in text:
        return "iris"
    if any(k in text for k in ("各社共通", "各社共用", "汎用", "共通タイプ")):
        return "universal"
    return "unknown"


def classify(group_by: str, title: str) -> str:
    if group_by == "sheet_size":
        return sheet_size(title)
    if group_by == "litter_material":
        return litter_material(title)
    if group_by == "compatibility":
        return compatibility(title)
    return "all"
