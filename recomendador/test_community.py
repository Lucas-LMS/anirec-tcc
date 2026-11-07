import copy,json,subprocess,unittest,shutil
from pathlib import Path
from community_recommendations import apply

def fixture():
 rows=[dict(key=str(i),anilist_id=i,base_score=.5,personalized_score=.6,is_seen=False,general_components={'content':.5},personal_components={'content':.6}) for i in range(1,6)]
 return dict(general=rows,personalized=rows[:4],diagnostics=[dict(key=r['key'],reason='eligible') for r in rows],params={})

class CommunityTests(unittest.TestCase):
 def test_absence_nonpositive_and_input_preservation(self):
  original=fixture();saved=copy.deepcopy(original)
  result=apply(original,dict(edges=[dict(target_id=1,rating=1),dict(target_id=2,rating=100),dict(target_id=3,rating=-2),dict(target_id=4,rating=0)]))
  by_id={r['anilist_id']:r for r in result['general']}
  for i in (3,4,5):self.assertEqual(by_id[i]['base_score'],.5)
  self.assertGreater(by_id[2]['base_score'],by_id[1]['base_score']);self.assertLess(by_id[1]['base_score']-.5,.01)
  self.assertEqual(original,saved);self.assertEqual(set(r['key'] for r in result['general']),set(r['key'] for r in original['general']))
  self.assertEqual(set(r['key'] for r in result['personalized']),set(r['key'] for r in original['personalized']))
  for row in result['general']:
   self.assertAlmostEqual(sum(row['general_components'].values()),row['base_score'])
   self.assertAlmostEqual(sum(row['personal_components'].values()),row['personalized_score'])
 def test_invalid_parameters(self):
  for weight in (-1,float('nan'),.6):
   with self.assertRaises(ValueError):apply(fixture(),{},weight)
 @unittest.skipUnless(shutil.which("node"),"Node is checked separately when unavailable in this Python environment")
 def test_javascript_parity(self):
  evidence=dict(anchor_id=9,edges=[dict(target_id=1,rating=103),dict(target_id=3,rating=-1)])
  source=Path(__file__).parent/'shared/community-core.js'
  script="const fs=require('fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(require(process.argv[1]).apply(x.result,x.evidence)));"
  actual=json.loads(subprocess.check_output(['node','-e',script,str(source.resolve())],input=json.dumps(dict(result=fixture(),evidence=evidence)).encode()))
  expected=apply(fixture(),evidence)
  for field in ['general','personalized']:
   self.assertEqual([r['key'] for r in actual[field]],[r['key'] for r in expected[field]])
   for a,b in zip(actual[field],expected[field]):
    self.assertAlmostEqual(a['base_score'],b['base_score']);self.assertAlmostEqual(a['personalized_score'],b['personalized_score'])
