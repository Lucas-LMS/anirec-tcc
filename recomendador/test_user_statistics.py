import unittest
from user_statistics import compute_statistics

RECORDS=[dict(key='a',anilist_id=1,genres=['Comedy'],tags=[{'name':'Yuri'}],episodes=12,duration=24),dict(key='b',anilist_id=2,genres=['Comedy'],tags=[],episodes=1,duration=95),dict(key='c',anilist_id=3,genres=['Drama'],tags=[{'name':'Yuri'}],episodes=None,duration=24),dict(key='d',anilist_id=4,genres=['Drama'],tags=[{'name':'Yuri'}],episodes=6,duration=None)]
ENTRIES=[dict(mediaId=1,status='COMPLETED',score=80,progress=12,repeat=1),dict(mediaId=2,status='PLANNING',score=0,progress=0),dict(mediaId=3,status='CURRENT',score=0,progress=3),dict(mediaId=4,status='COMPLETED',score=90,progress=6)]

class StatisticsTests(unittest.TestCase):
    def test_completed_mean_repeats_and_unknown_runtime(self):
        r=compute_statistics(RECORDS,ENTRIES);self.assertEqual(r['count'],2);self.assertEqual(r['summary']['meanScore'],85);self.assertEqual(r['summary']['watched_minutes_estimated'],576);self.assertEqual(r['summary']['watched_unknown'],1)
        y=r['tags'][0];self.assertEqual(y['count'],2);self.assertEqual(y['meanScore'],85)
    def test_planning_is_not_watched_and_unrated_is_not_zero_mean(self):
        r=compute_statistics(RECORDS,ENTRIES,'PLANNING');self.assertIsNone(r['summary']['meanScore']);self.assertEqual(r['summary']['watched_minutes_estimated'],0);self.assertEqual(r['summary']['catalog_minutes_estimated'],95)
    def test_all_statuses_deduplicate_and_keep_missing_fields(self):
        r=compute_statistics(RECORDS,ENTRIES+[ENTRIES[0]],'ALL');self.assertEqual(r['total_entries'],4);self.assertEqual(r['summary']['watched_minutes_estimated'],648);self.assertEqual(r['summary']['catalog_minutes_estimated'],383);self.assertEqual(r['summary']['catalog_unknown'],2)

if __name__=='__main__':unittest.main()
