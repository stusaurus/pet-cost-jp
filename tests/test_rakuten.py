import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common.rakuten import fetch_items

class RakutenLookupTest(unittest.TestCase):
    def test_shop_lookup_keeps_existing_request_and_affiliate_contract(self):
        captured=[]
        def response(request):
            captured.append(parse_qs(urlparse(request.full_url).query))
            return {'items':[{'itemName':'fixture','itemPrice':1200,'affiliateUrl':'https://hb.afl.rakuten.co.jp/hgc/fixture/','shopName':'fixture','postageFlag':0}]}
        with patch.dict('os.environ',{'RAKUTEN_APPLICATION_ID':'fixture-app','RAKUTEN_ACCESS_KEY':'fixture-key','RAKUTEN_AFFILIATE_ID':'fixture-affiliate'},clear=True),patch('common.rakuten._open_json',side_effect=response):
            old=fetch_items('fixture',pages=1)
            new=fetch_items('fixture',pages=1,shop_code='sweet-pet')
        self.assertNotIn('shopCode',captured[0])
        self.assertEqual(captured[1].pop('shopCode'),['sweet-pet'])
        self.assertEqual(captured[0],captured[1])
        self.assertEqual(old,new)
        self.assertEqual(new[0]['url'],'https://hb.afl.rakuten.co.jp/hgc/fixture/')

if __name__=='__main__':unittest.main()
