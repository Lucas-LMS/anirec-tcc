"""Meaningful regression tests with temporary profiles and NO network calls."""
import json,tempfile,unittest
import numpy as np
from engine import Engine

class OfflineClient:
    def candidates(self,media_id):return []
    def search(self,text):return []

class IRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.engine=Engine(client=OfflineClient(),data_dir=cls.temp.name)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.e=self.engine
        self.e.profile=dict(username=None,entries=[],user=None,manual_favorites=[],preferred=[],avoided=[],rejected=[],truncated=False)
        self.e.live_media.clear();self.e.restore_profile_media()
        self.e.discovery_extra.clear()
    def test_explicit_discovery_enters_candidate_pool(self):
        item=self.e.add_anilist(dict(id=999999999,title={'english':'Extra candidate'},description='Action adventure mystery with friends and secrets.',genres=['Action'],tags=[],type='ANIME',status='FINISHED'))
        self.e.discovery_extra['mal:47']=[item['key']]
        result=self.e.recommend('mal:47',online=False)
        self.assertEqual(result['candidate_count'],len(self.e.base_keys)+1)
        self.assertIn(item['key'],[row['key'] for row in result['general']])
    def test_pure_mode_ignores_saved_profile_and_preserves_it(self):
        before=self.e.recommend('mal:47',online=False,pure=True)
        self.e.onboarding(['Yuri'],['Action'],['mal:144'])
        self.e.reject(before['general'][0]['key'])
        saved=json.dumps(self.e.profile,sort_keys=True)
        after=self.e.recommend('mal:47',online=False,pure=True)
        self.assertEqual([r['key'] for r in before['general']],[r['key'] for r in after['general']])
        np.testing.assert_allclose([r['base_score'] for r in before['general']],[r['base_score'] for r in after['general']])
        self.assertEqual(after['personalization'],0);self.assertFalse(after['profile_active'])
        self.assertEqual(json.dumps(self.e.profile,sort_keys=True),saved)
    def test_portable_vectors_match_existing_model(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'ANIREC_WORD2VEC_PATH':directory+'/absent.model'}):
            portable=Engine(client=OfflineClient(),data_dir=directory)
            np.testing.assert_array_equal(self.e.words['the'],portable.words['the'])
    def test_no_profile_and_zero_weight(self):
        r=self.e.recommend('mal:47',online=False,exclude_seen=False)
        self.assertFalse(r['profile_active']);self.assertEqual(r['general'],r['personalized'])
        self.e.favorite('mal:144');self.e.preferences(['Romance'],[])
        r=self.e.recommend('mal:47',personalization=0,online=False,exclude_seen=False)
        self.assertEqual([i['key'] for i in r['general']],[i['key'] for i in r['personalized']])
        self.assertNotIn('mal:47',[i['key'] for i in r['general']])
    def test_onboarding_without_notes_and_two_lists(self):
        favorite_keys=['mal:144','mal:387','mal:54']
        summary=self.e.onboarding(['Action','Drama','Yuri'],[],favorite_keys)
        self.assertEqual(summary['rated_count'],0);self.assertEqual(summary['positive_count'],3)
        self.assertEqual(len(summary['manual_favorites']),3)
        r=self.e.recommend('mal:47',online=False,personal_min_topics=0)
        self.assertTrue(r['profile_active'])
        for name,items in r['recommendation_sets'].items():
            self.assertLessEqual(len(items),10)
            if name.endswith('unseen'):self.assertTrue(all(not item['is_seen'] for item in items))
        before=self.e.profile.copy()
        with self.assertRaises(ValueError):self.e.onboarding(['Changed'],[],['missing:key'])
        self.assertEqual(self.e.profile,before)
    def test_synopsis_contribution_and_metadata_coverage(self):
        self.e.favorite('mal:144');self.e.preferences(['Romance'],[])
        r=self.e.recommend('mal:47',online=False,exclude_seen=False)
        for item in r['personalized']:
            self.assertAlmostEqual(sum(item['contributions'].values()),item['personalized_score'],places=7)
            self.assertGreater(item['contributions']['anchor_text'],0)
            q=item['quality']
            self.assertEqual(q['known_words']+q['unknown_words'],q['word_count'])
        self.assertEqual(r['metadata_coverage']['total'],len(self.e.base_keys))
        self.assertEqual(self.e.text_quality(dict(text='zzzzzznotaword'))['vocabulary_coverage'],0)
        # Hold tags/genres fixed: the synopsis alone changes the vector.
        a=dict(key='fixture:a',text='school girl friendship',genres=['Action'],tags=[])
        b=dict(key='fixture:b',text='war military battle',genres=['Action'],tags=[])
        self.assertFalse(np.allclose(self.e.vector(a),self.e.vector(b)))
    def test_low_ratings_repel_and_user_midrange_is_neutral(self):
        self.e.profile['entries']=[dict(status='DROPPED',score=20,media=dict(id=900047,idMal=47)),dict(status='COMPLETED',score=35,media=dict(id=900144,idMal=144)),dict(status='COMPLETED',score=50,media=dict(id=900387,idMal=387))]
        self.e.restore_profile_media();vector,_,_,info=self.e.profile_signals()
        self.assertEqual(info['rated_count'],3);self.assertEqual(info['negative_count'],1)
        self.assertEqual(info['neutral_count'],1);self.assertEqual(info['vector_count'],2)
        self.assertTrue(np.allclose(vector, __import__('engine').unit(self.e.vector(self.e.base_media['mal:387'])-self.e.vector(self.e.base_media['mal:47']))))
        self.assertEqual(info['rating_neutral'],35)
    def test_observed_five_to_ten_has_neutral_seven_point_five(self):
        self.e.profile['entries']=[dict(status='COMPLETED',score=s,media=dict(id=900000+i,idMal=m)) for i,(s,m) in enumerate([(50,47),(75,144),(100,387)])]
        self.e.restore_profile_media();_,_,_,info=self.e.profile_signals()
        self.assertEqual(info['rating_neutral'],75);self.assertEqual(info['negative_count'],1)
        self.assertEqual(info['positive_count'],1);self.assertEqual(info['neutral_count'],1)
        self.e.profile['entries']=[dict(status='COMPLETED',score=80,media=dict(id=900047,idMal=47))]
        vector,_,_,info=self.e.profile_signals();self.assertIsNone(vector)
        self.assertFalse(info['rating_scale_informative'])
    def test_negative_volume_does_not_flip_positive_centroid(self):
        low=self.e.base_media['mal:47'];high=self.e.base_media['mal:387']
        self.e.profile['entries']=[dict(status='COMPLETED',score=20,media=dict(id=710000+i,title=dict(english='Low fixture'),description=low['text'],genres=low['genres'],tags=[])) for i in range(50)]
        self.e.profile['entries'].append(dict(status='COMPLETED',score=80,media=dict(id=900387,idMal=387,title=dict(english=high['title']),description=high['text'],genres=high['genres'],tags=high['tags'])))
        self.e.restore_profile_media()
        r=self.e.recommend('mal:144',online=False,exclude_seen=False,personal_min_topics=0)
        positive=next(x for x in r['general'] if x['key']=='mal:387')
        negative=next(x for x in r['general'] if x['key']=='mal:47')
        self.assertGreater(positive['profile_text_score'],.5)
        self.assertLess(negative['profile_text_score'],.5)
        self.assertLessEqual(r['personal_eligible_count'],r['eligible_count'])
        with self.assertRaises(ValueError):self.e.recommend('mal:47',online=False,personal_min_topics=float('nan'))
    def test_entire_synopsis_and_late_words_change_vector(self):
        description=('school ' * 100)+'military war battle'
        item=self.e.materialize(dict(id=799999,title=dict(english='Fixture'),description=description,genres=[],tags=[]))
        self.assertTrue(item['text'].endswith('military war battle'))
        self.assertGreater(len(item['text'].split()),80)
        shortened=dict(item,text='school '*80)
        self.assertFalse(np.allclose(self.e.vector(item),self.e.vector(shortened)))
        self.assertTrue(any(len(m['text'].split())>80 for m in self.e.base_media.values()))
        for m in self.e.base_media.values():self.assertTrue(m['synopsis_complete'])
    def test_missing_rating_is_not_approval_but_every_scored_item_counts(self):
        # Fixture IDs are intentionally artificial AniList IDs, not live user data.
        self.e.profile.update(user=dict(favourites=dict(anime=dict(nodes=[dict(id=900054)]))),entries=[
            dict(status='COMPLETED',score=0,media=dict(id=900047,idMal=47)),
            dict(status='PLANNING',score=100,media=dict(id=900144,idMal=144)),
            dict(status='COMPLETED',score=80,media=dict(id=900387,idMal=387)),
            dict(status='COMPLETED',score=0,media=dict(id=900054,idMal=54))])
        self.e.restore_profile_media();vector,_,seen,info=self.e.profile_signals()
        self.assertEqual(info['positive_count'],2);self.assertEqual(info['vector_count'],3)
        self.assertIn('mal:47',seen);self.assertNotIn('mal:144',seen);self.assertIsNotNone(vector)
    def test_score_decomposition_and_limit(self):
        self.e.favorite('mal:144');self.e.preferences(['Romance'],[])
        r=self.e.recommend('mal:47',personalization=.35,online=False,exclude_seen=False)
        for item in r['personalized']:
            base=.5*(item['anchor_cosine']+1)/2+.5*item['anchor_topic_overlap']
            affinity=.7*item['profile_text_score']+.3*item['preference_affinity']
            self.assertAlmostEqual(item['base_score'],base,places=12)
            self.assertAlmostEqual(item['personalized_score'],.65*base+.35*affinity,places=12)
        self.assertEqual(self.e.recommend('mal:47',personalization=5,online=False)['personalization'],.6)
        with self.assertRaises(ValueError):self.e.recommend('mal:47',personalization=float('nan'),online=False)
    def test_hide_restore_and_explicit_filter(self):
        first=self.e.recommend('mal:47',online=False,exclude_seen=False)['general'][0]['key']
        self.e.reject(first)
        self.assertNotIn(first,[m['key'] for m in self.e.recommend('mal:47',online=False,exclude_seen=False)['general']])
        self.e.reject(first,False)
        self.assertEqual(first,self.e.recommend('mal:47',online=False,exclude_seen=False)['general'][0]['key'])
        self.e.preferences([],['Action'])
        self.assertTrue(all('Action' not in m['genres'] for m in self.e.recommend('mal:47',online=False)['general']))
    def test_profile_does_not_depend_on_browsing_cache(self):
        self.e.favorite('mal:144');before=self.e.profile_signals()[0].copy()
        # A later fetched synopsis for the same entity must not rewrite saved preference signals.
        self.e.add_anilist(dict(id=900144,idMal=144,title=dict(english='Fixture'),description=self.e.base_media['mal:47']['text'],genres=['Action'],tags=[]))
        self.assertTrue(np.allclose(before,self.e.profile_signals()[0]))
        restored=Engine(client=OfflineClient(),data_dir=self.temp.name)
        self.assertTrue(np.allclose(before,restored.profile_signals()[0]))
    def test_exclusion_including_spoilers_and_missing_tags(self):
        source=self.e.base_media['mal:47']
        def candidate(i,tags):return dict(id=700000+i,title=dict(english='Fixture '+str(i)),description=source['text'],genres=source['genres'],tags=tags,type='ANIME')
        related=[candidate(1,[dict(name='Male Protagonist',rank=90,isGeneralSpoiler=True)]),candidate(2,[]),candidate(3,[dict(name='Female Protagonist',rank=90)])]
        class Related(OfflineClient):
            def candidates(self,media_id):return related
        self.e.client=Related();self.e.add_anilist(dict(id=900047,idMal=47,title=dict(english=source['title']),description=source['text'],genres=source['genres'],tags=[]))
        self.e.preferences([],['Male Protagonist'])
        original_keys=self.e.base_keys;self.e.base_keys=set()
        try:
            loose=self.e.recommend('mal:47',online=True,exclude_seen=False)
            strict=self.e.recommend('mal:47',online=True,exclude_seen=False,require_tag_metadata=True)
            self.assertEqual(loose['excluded_by_topic'],1)
            self.assertGreater(strict['excluded_unknown_tags'],0)
            self.assertEqual([r['key'] for r in strict['general']],['anilist:700003'])
        finally:self.e.client=OfflineClient();self.e.base_keys=original_keys
    def test_large_profile_and_twenty_related_candidates(self):
        # Regression: a large profile previously evicted candidates while composing a pool.
        self.e.profile['entries']=[dict(status='PLANNING',score=0,media=dict(id=800000+i,idMal=None)) for i in range(3000)]
        source=self.e.base_media['mal:47']
        related=[dict(id=700000+i,idMal=None,title=dict(english='Fixture '+str(i)),description=source['text'],genres=['Action'],tags=[]) for i in range(20)]
        class Related(OfflineClient):
            def candidates(self,media_id):return related
        self.e.client=Related();self.e.add_anilist(dict(id=900047,idMal=47,title=dict(english=source['title']),description=source['text'],genres=source['genres'],tags=[]))
        r=self.e.recommend('mal:47',online=True,exclude_seen=False)
        self.assertEqual(r['related_count'],20);self.assertEqual(r['candidate_count'],len(self.e.base_keys)+20)
        self.assertTrue(all('anilist:'+str(700000+i) in self.e.media for i in range(20)))
        self.e.client=OfflineClient()

if __name__=='__main__':unittest.main(verbosity=2)
