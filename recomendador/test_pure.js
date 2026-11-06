const assert=require('node:assert/strict'),fs=require('node:fs'),ir=require('./shared/ir-core.js');
const c=JSON.parse(fs.readFileSync(process.argv[2],'utf8'))[0].input;
const baseline=ir.rank({...c,pure:true,ratings:{},favorites:[],preferred:[],avoided:[],hidden:[],seenIds:[]});
const poisoned=ir.rank({...c,pure:true,ratings:Object.fromEntries(c.records.map(r=>[r.key,1])),favorites:c.records.map(r=>r.key),preferred:['Yuri'],avoided:c.anchor.genres,hidden:c.records.map(r=>r.key),seenIds:c.records.map(r=>r.anilist_id)});
assert.deepEqual(poisoned.general.map(r=>[r.key,r.base_score]),baseline.general.map(r=>[r.key,r.base_score]));assert.equal(poisoned.personalization,0);assert.equal(poisoned.profile_active,false);assert.ok(poisoned.general.every(r=>!r.is_seen));console.log('Pure mode ignores all profile signals: PASS');
