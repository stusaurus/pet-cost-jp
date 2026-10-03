import json
import math
import urllib.parse
from collections import Counter
from pathlib import Path

from common.classify import classify
from common.engine import _family_key, category_matches, parse_quantity
from common.quantity import normalize_text
from common.catalog import audit as audit_catalog
from decisions import regression_errors

ROOT = Path(__file__).resolve().parents[1]
SITE_DATA = ROOT / "site" / "data"
CATEGORIES = json.loads((ROOT / "config" / "categories.json").read_text(encoding="utf-8"))

FORBIDDEN = (
    "ふるさと納税", "定期便", "中古", "訳あり", "訳アリ",
    "アウトレット", "展示品", "開封品", "箱潰れ", "箱つぶれ", "b品",
)


def direct_rakuten_url(affiliate_url):
    try:
        parsed = urllib.parse.urlparse(affiliate_url)
        if parsed.netloc != "hb.afl.rakuten.co.jp":
            return ""
        query = urllib.parse.parse_qs(parsed.query)
        direct = query.get("pc", [""])[0]
        if direct.startswith("https://item.rakuten.co.jp/"):
            return direct
    except Exception:
        pass
    return ""


def main():
    errors = []
    all_ids = []
    total = 0
    summary = {}

    for category in CATEGORIES:
        path = SITE_DATA / f"{category['id']}.json"
        if not path.exists():
            errors.append(f"{category['id']}: data file missing")
            continue

        payload = json.loads(path.read_text(encoding="utf-8"))
        items = payload.get("items", [])
        total += len(items)
        summary[category["id"]] = len(items)

        if not items:
            errors.append(f"{category['id']}: no publishable items")

        allowed_groups = set(category.get("groups", {}).keys()) | {"all"}
        family_counts = Counter()

        for index, item in enumerate(items, 1):
            label = f"{category['id']}#{index}"
            title = item.get("name", "")
            all_ids.append(item.get("product_id", ""))

            if not category_matches(title, category):
                errors.append(f"{label}: category mismatch: {title}")

            forbidden = [word for word in FORBIDDEN if normalize_text(word) in normalize_text(title)]
            if forbidden:
                errors.append(f"{label}: forbidden listing term {forbidden[0]}")

            parsed = parse_quantity(title, category["parser"])
            if not parsed:
                errors.append(f"{label}: quantity no longer parses safely")
            else:
                actual_q = float(item.get("quantity") or 0)
                if not math.isclose(actual_q, float(parsed["quantity"]), rel_tol=0, abs_tol=1e-6):
                    errors.append(
                        f"{label}: quantity mismatch stored={actual_q} parsed={parsed['quantity']}"
                    )

            group = item.get("group", "")
            expected_group = classify(category.get("group_by", ""), title)
            if group == "ambiguous" or expected_group == "ambiguous":
                errors.append(f"{label}: ambiguous classification")
            elif group != expected_group:
                errors.append(f"{label}: group mismatch stored={group} expected={expected_group}")
            if group not in allowed_groups:
                errors.append(f"{label}: unknown group {group}")

            price = float(item.get("price") or 0)
            quantity = float(item.get("quantity") or 0)
            unit_price = float(item.get("unit_price") or 0)
            if price <= 0 or quantity <= 0:
                errors.append(f"{label}: invalid price/quantity")
            elif not math.isclose(unit_price, price / quantity, rel_tol=0, abs_tol=0.00011):
                errors.append(
                    f"{label}: unit price mismatch {unit_price} != {price}/{quantity}"
                )
            if not all(math.isfinite(v) for v in (price, quantity, unit_price)):
                errors.append(f'{label}: non-finite numeric value')
            lower = 5 if category['metric'] == 'per_liter' else .5
            if not lower <= unit_price <= 10000:
                errors.append(f'{label}: implausible unit price; requires review')

            if not direct_rakuten_url(item.get("url", "")):
                errors.append(f"{label}: affiliate URL has no valid Rakuten item target")

            family = _family_key(item, category)
            if family:
                family_counts[family] += 1

        for family, count in family_counts.items():
            if count > 2:
                errors.append(
                    f"{category['id']}: product family {family} occupies {count} rows"
                )

    ids = [x for x in all_ids if x]
    duplicate_ids = [k for k, v in Counter(ids).items() if v > 1]
    if duplicate_ids:
        errors.append(f"duplicate product_id: {', '.join(duplicate_ids)}")

    discovery_path = SITE_DATA / 'discovery.json'
    if discovery_path.exists():
        discovery_data = json.loads(discovery_path.read_text())
        errors.extend(audit_catalog(discovery_data, json.loads((ROOT / 'config/discovery.json').read_text())))
        for key, payload in discovery_data.items():
            summary[key] = len(payload.get('items',[]))
            total += summary[key]
    else:
        errors.append('discovery data missing')
    errors.extend(regression_errors(ROOT / 'site', ROOT / 'data'))
    if errors:
        print("PRODUCT QUALITY AUDIT FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("PRODUCT QUALITY AUDIT PASSED")
    print(f"Total published items: {total}")
    for key, count in summary.items():
        print(f"- {key}: {count}")


if __name__ == "__main__":
    main()
