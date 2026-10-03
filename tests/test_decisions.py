import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from decisions import regression_errors, enrich
from common.quantity import parse_liters, parse_100g, parse_count
from common.engine import category_matches

class DecisionQualityTests(unittest.TestCase):
    def test_ambiguous_quantities_do_not_enter_comparison(self):
        for title in ['猫砂 5L お徳用 4袋', '猫砂 40L 5L×8袋 7L']:
            self.assertIsNone(parse_liters(title))
        for title in ['フード 2kg お徳用 4袋', 'フード 2kg×2袋 おまけ800g']:
            self.assertIsNone(parse_100g(title))
        self.assertIsNone(parse_count('シーツ 800枚 200枚×4袋 300枚'))
        self.assertEqual(parse_liters('猫砂 5L×4袋')['quantity'],20)
        self.assertEqual(parse_100g('フード 4kg (2kg×2袋)')['quantity'],40)

    def test_special_prices_are_excluded(self):
        for phrase in ['定期購入','初回限定','初回のみ','会員限定価格']:
            self.assertFalse(category_matches('ペットシーツ 100枚 '+phrase,{'include_any':['ペットシーツ']}))

    def test_count_and_condition_regressions_block_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); site=root/'site'; prior=root/'prior'; (site/'data').mkdir(parents=True);prior.mkdir()
            (prior/'pet-sheets.json').write_text(json.dumps({'items':[{'group':'regular'}]*8+[{'group':'wide'}]*2}))
            (site/'data/pet-sheets.json').write_text(json.dumps({'items':[{'group':'regular'}]*3}))
            errors=regression_errors(site,prior)
            self.assertTrue(any('count dropped' in e for e in errors));self.assertTrue(any('disappeared' in e for e in errors))

    def test_history_records_observations_without_fabricating_days(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);site=root/'site';prior=root/'prior';(site/'data').mkdir(parents=True);prior.mkdir();(site/'categories').mkdir();(site/'index.html').write_text('<main></main><body></body>')
            row={'name':'シーツ100枚','product_id':'p1','url':'https://hb.afl.rakuten.co.jp/hgc/id/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fshop%2Fa%2F','group':'regular','quantity':100,'price':1000,'unit_price':10}
            payload={'updated':'2026-10-01 06:20 JST','category':{'metric_label':'1枚'},'items':[row]}
            path=site/'data/pet-sheets.json';path.write_text(json.dumps(payload));enrich(site,prior)
            first=json.loads((site/'data/price-history.json').read_text());self.assertEqual(len(next(iter(first.values()))),1)
            (prior/'price-history.json').write_text(json.dumps(first));payload['updated']='2026-10-03 06:20 JST';row['price']=900;row['unit_price']=9;path.write_text(json.dumps(payload));enrich(site,prior)
            dates=[h['date'] for h in next(iter(json.loads((site/'data/price-history.json').read_text()).values()))];self.assertEqual(dates,['2026-10-01','2026-10-03'])
