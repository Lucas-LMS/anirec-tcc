import unittest
from history_profile import history_preferences

class HistoryTests(unittest.TestCase):
    def test_frequency_dominates_moderate_rating_and_no_top_thirty_limit(self):
        records=[dict(key='a',anilist_id=1,genres=['Comedy'],tags=[{'name':'Tag '+str(i)} for i in range(45)])]
        stats={'count':2500,'genres':[{'genre':'Comedy','count':1282,'meanScore':70.56}],'tags':[{'tag':{'name':'Primarily Female Cast'},'count':1030,'meanScore':72.45}]}
        values=history_preferences(records,{'a':70},[],[1],stats,75,25)
        self.assertGreater(values['comedy']['weight'],0)
        self.assertGreater(values['primarily female cast']['weight'],0)
        self.assertIn('tag 44',values)
        self.assertEqual(values['comedy']['count'],1282)
    def test_zero_mean_is_missing_not_disapproval_and_tiny_counts_shrink(self):
        stats={'count':100,'tags':[{'tag':{'name':'Unrated'},'count':1,'meanScore':0}]}
        value=history_preferences([],{},[],[],stats,75,25)['unrated']
        self.assertIsNone(value['mean_score']);self.assertEqual(value['rating_quality'],0)
        self.assertGreater(value['weight'],0);self.assertLess(value['weight'],.02)

if __name__=='__main__':unittest.main()
