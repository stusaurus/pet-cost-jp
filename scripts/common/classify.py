from .quantity import normalize_text


def sheet_size(title: str) -> str:
    text = normalize_text(title)
    found = set()
    if "スーパーワイド" in text or "super wide" in text:
        found.add("super_wide")
    without_super = text.replace("スーパーワイド", "").replace("super wide", "")
    if "ワイド" in without_super or "wide" in without_super:
        found.add("wide")
    if "レギュラー" in text or "regular" in text:
        found.add("regular")
    if len(found) > 1:
        return "ambiguous"
    if found:
        return next(iter(found))
    return "unknown"


def litter_material(title: str) -> str:
    text = normalize_text(title)

    # Usage type takes priority for products explicitly made for a system toilet.
    if any(k in text for k in ("システムトイレ", "デオトイレ", "ニャンとも")):
        return "system"

    signals = set()
    if any(k in text for k in ("ベントナイト", "鉱物")):
        signals.add("mineral")
    if any(k in text for k in ("おから", "豆腐", "とうふ")):
        signals.add("okara")
    if any(k in text for k in ("ひのき", "ヒノキ", "木製", "木の", "木質", "パイン", "ウッド")):
        signals.add("wood")
    if any(k in text for k in ("シリカ", "silica")):
        signals.add("silica")
    if any(k in text for k in ("紙製", "紙の", "ペーパー")):
        signals.add("paper")

    if len(signals) > 1:
        return "mixed"
    if signals:
        return next(iter(signals))
    return "unknown"


def compatibility(title: str) -> str:
    text = normalize_text(title)

    # Current Raclean sheets are sold as "各社共通"; classify compatibility,
    # not the manufacturer name.
    if any(k in text for k in ("各社共通", "各社共用", "汎用", "共通タイプ", "ラクリーン", "raclean")):
        return "universal"
    if "デオトイレ" in text:
        return "deotoilet"
    if "ニャンとも" in text or "にゃんとも" in text:
        return "nyantomo"
    if "アイリス" in text or "tih-" in text or "s-ss" in text:
        return "iris"
    return "unknown"


def classify(group_by: str, title: str) -> str:
    if group_by == "sheet_size":
        return sheet_size(title)
    if group_by == "litter_material":
        return litter_material(title)
    if group_by == "compatibility":
        return compatibility(title)
    return "all"
