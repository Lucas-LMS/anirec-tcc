import unittest,math
from retrieval_experiments import bm25,quality,apply,study
class ExperimentTests(unittest.TestCase):
    def test_bm25_specific_terms_and_no_match(self):
        rows=[{'key':'a','text':'cyborg police city investigation'},{'key':'b','text':'cyborg police investigation team'},{'key':'c','text':'cooking camping forest lake'}]
        result=bm25(rows,rows[0]['text'])
        self.assertGreater(result['b']['score'],result['c']['score']);self.assertEqual(result['c']['raw'],0)
        self.assertTrue(all(0<=v['score']<=1 for v in result.values()))
        self.assertTrue(all(v['score']==0 for v in bm25(rows,'absentunique').values()))
    def test_community_weighted_precedes_mean_and_missing_is_missing(self):
        self.assertEqual(quality({'average_score':80,'mean_score':95}),(.8,'average_score'))
        self.assertEqual(quality({'average_score':None,'mean_score':70}),(.7,'mean_score'))
        self.assertEqual(quality({'popularity':999999}), (None,None))
        self.assertEqual(quality({'average_score':float('nan')}),(None,None))
    def test_bounded_bonus_and_decomposition(self):
        row=dict(key='b',title='B',text='police cyborg',anchor_cosine=.4,anchor_topic_overlap=.3,average_score=90,contributions={'profile_text':.1,'profile_topics':.02},is_seen=False)
        base=dict(anchor={'text':'police cyborg'},general=[row],personalized=[row],personalization=.35,diagnostics=[{'key':'b','reason':'eligible'}],params={})
        data=[{'key':'a','text':'police cyborg'},row]
        off=apply(base,data,'vectors',0);on=apply(base,data,'hybrid',.05)
        r=on['general'][0];self.assertAlmostEqual(sum(r['general_components'].values()),r['base_score']);self.assertAlmostEqual(sum(r['personal_components'].values()),r['personalized_score'])
        self.assertLessEqual(r['general_components']['community'],.05);self.assertLessEqual(r['base_score'],1)
        self.assertAlmostEqual(off['general'][0]['base_score'],.5)
        with self.assertRaises(ValueError):apply(base,data,'vectors',.5)
    def test_preference_study_excludes_seen_and_profile_ratings(self):
        rows=[dict(key=key,title=key,text='police city investigation',anchor_cosine=.8,anchor_topic_overlap=.8,contributions={'profile_text':.1,'profile_topics':.02},is_seen=key=='favorite') for key in ['rated','favorite','unseen']]
        source=dict(anchor={'key':'anchor','text':'police city'},general=rows,personalized=rows,personalization=.35,diagnostics=[{'key':r['key'],'reason':'eligible'} for r in rows],params={},profile_active=True,filters={'pure':False},candidate_count=4)
        result=study(source,[{'key':'anchor','text':'police city'}]+rows,evaluation_excluded={'rated'})
        self.assertEqual(result['preference_pool_keys'],['unseen'])
        self.assertIn('rated',result['similarity_pool_keys'])
        self.assertTrue(all([r['key'] for r in system['personalized']]==['unseen'] for system in result['systems']))
if __name__=='__main__':unittest.main()
