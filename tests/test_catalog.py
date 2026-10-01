import json
import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common.catalog import inspect, collect, audit
ROOT=Path(__file__).resolve().parents[1]

class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/'config/discovery.json').read_text())
        self.row={'name':'犬用 おもちゃ ロープ 小型犬 12cm', 'price':980, 'shop':'test', 'url':'https://hb.afl.rakuten.co.jp/hgc/test/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Ftest%2Fone%2F'}
    def test_evidence_and_no_price_rank(self):
        a,reason=inspect(self.row,self.config['dog-toys'])
        self.assertFalse(reason);self.assertEqual(a['size'],'small');self.assertEqual(a['play'],'together');self.assertEqual(a['age'],'')
        for e in a['evidence']:self.assertIn(e['quote'],self.row['name'])
        self.assertNotIn('unit_price',a)
        self.assertEqual(len(collect([self.row,self.row],{**self.config['dog-toys'],'publish_products':False})['items']),1)
    def test_reject_uncertain_products(self):
        for title in ['猫 犬 おもちゃ ロープ 12cm','犬 おもちゃ ボール ロープ 12cm','犬 おもちゃ ロープ','犬 おもちゃ ロープ 選べる 12cm','中古 犬 おもちゃ ロープ 12cm','犬 おもちゃ ロープ 成犬 シニア 12cm']:
            self.assertIsNone(inspect({**self.row,'name':title},self.config['dog-toys'])[0],title)
    def test_food_gate_and_medical_rejection(self):
        base={**self.row,'name':'ドッグフード ドライ 総合栄養食 成犬用 2kg'}
        candidate,reason=inspect(base,self.config['dog-food'])
        self.assertTrue(candidate);self.assertEqual(reason,'要メーカー照合')
        self.assertEqual(collect([base],self.config['dog-food'])['items'],[])
        for term in ['療法食','腎臓病','アレルギー','減量','おやつ']:
            self.assertIsNone(inspect({**base,'name':base['name']+term},self.config['dog-food'])[0])
        self.assertTrue(audit({'dog-food':{'items':[candidate]}},self.config))
    def test_audit_detects_fabricated_attributes(self):
        a,_=inspect(self.row,self.config['dog-toys'])
        review={'reviewed_on':date.today().isoformat(),'required_title_terms':['ロープ','12cm'],'play':'together','age':'','size':'small','dimensions':'12cm','label':'ロープトイ','warning':'見守りのもとで使用','source':'https://item.rakuten.co.jp/test/one/'}
        approved={**self.config,'dog-toys':{**self.config['dog-toys'],'publish_products':True,'approved_products':{'https://item.rakuten.co.jp/test/one/':review}}}
        a=collect([self.row],approved['dog-toys'])['items'][0]
        self.assertFalse(audit({'dog-toys':{'items':[a]}},approved))
        self.assertTrue(audit({'dog-toys':{'items':[{**a,'age':'senior'}]}},self.config))
        self.assertEqual(collect([self.row],self.config['dog-toys'])['items'],[])
        expired={**approved['dog-toys'],'approved_products':{'https://item.rakuten.co.jp/test/one/':{**review,'reviewed_on':'2020-01-01'}}}
        self.assertEqual(collect([self.row],expired)['items'],[])
        self.assertTrue(audit({'dog-toys':{'items':[{**a,'review_warning':'絶対壊れない'}]}},approved))

if __name__=='__main__':unittest.main()
