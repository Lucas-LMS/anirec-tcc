import unittest
from affinity import theme_affinity
class AffinityTests(unittest.TestCase):
    def test_unmatched_negative_does_not_dilute_a_positive_match(self):
        item={'yuri':dict(weight=.7)};positive={'yuri':dict(name='Yuri',weight=1,source='preferência explícita')}
        a=theme_affinity(positive,item)
        b=theme_affinity(dict(positive,mecha=dict(name='Mecha',weight=-100)),item)
        self.assertAlmostEqual(a['score'],.7);self.assertEqual(a['score'],b['score'])
        self.assertEqual(a['matched_explicit'],['Yuri'])
    def test_matched_aversion_reduces_coverage(self):
        preferences={'yuri':dict(name='Yuri',weight=1),'mecha':dict(name='Mecha',weight=-1)}
        self.assertEqual(theme_affinity(preferences,{'yuri':dict(weight=1)})['score'],1)
        self.assertEqual(theme_affinity(preferences,{'yuri':dict(weight=1),'mecha':dict(weight=1)})['score'],0)
    def test_missing_positive_is_not_a_match(self):
        self.assertEqual(theme_affinity({'yuri':dict(name='Yuri',weight=1)}, {})['score'],0)
        self.assertEqual(theme_affinity({}, {})['score'],0)
if __name__=='__main__':unittest.main()
