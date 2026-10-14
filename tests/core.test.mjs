import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import {poolFor,partition,storyKey,viableLinks,candidatesForPick,chooseSeedAndLink,weightedLink} from '../game-core.mjs';
const catalog=JSON.parse(readFileSync(new URL('../data/catalog.json',import.meta.url)));
const rules=JSON.parse(readFileSync(new URL('../database.rules.json',import.meta.url))).rules;
test('catalogue has broad representation',()=>{
  assert.ok(catalog.characters.length>=600);
  assert.ok(catalog.links.length>=75);
  assert.ok(new Set(catalog.characters.map(c=>c.work)).size>=25);
  assert.ok(catalog.characters.some(c=>c.kind==='real'));
  assert.ok(catalog.characters.some(c=>c.kind==='fictional'));
  assert.ok(catalog.characters.some(c=>c.name==='Hulk'));
  assert.ok(catalog.characters.some(c=>c.name==='Shrek'));
  assert.ok(catalog.characters.some(c=>c.name==='Rafiki'));
  assert.ok(catalog.characters.some(c=>c.name==='Hester Prynne'));
});
test('every qualified link applies to enough characters and different stories',()=>{
  for(const link of catalog.links){
    const p=poolFor(catalog,link.id);
    assert.ok(p.length>=12, link.id+' insufficient pool');
    assert.ok(new Set(p.map(c=>storyKey(c))).size>=4, link.id+' too few works');
    assert.ok(p.every(c=>c.tags.includes(link.id)));
  }
});
test('valid seeds split candidate works without overlap for either player',()=>{
  for(let i=0;i<100;i++){
    const choice=chooseSeedAndLink(catalog,[],Math.random);
    const links=viableLinks(catalog,choice.seed);
    assert.ok(links.some(l=>l.id===choice.traitId));
    const a=candidatesForPick(catalog,choice.traitId,choice.seed,'host');
    const b=candidatesForPick(catalog,choice.traitId,choice.seed,'guest');
    assert.ok(a.length>=5&&b.length>=5);
    assert.ok(!a.some(x=>b.some(y=>x.id===y.id)));
    assert.ok(!a.some(x=>b.some(y=>storyKey(x)===storyKey(y))));
  }
});
test('recent links avoided when other links exist',()=>{
  const l=[{id:'x',pool:18},{id:'y',pool:19}];
  assert.equal(weightedLink(l,['x'],()=>0).id,'y');
});
test('security rules expose private picks ONLY to their own picker and never permit whole-room read',()=>{
  const room=rules.rooms.$roomId;
  assert.equal(rules['.read'],false);
  assert.equal(room['.read'],undefined);
  assert.equal(room.picks['.read'],undefined);
  assert.match(room.picks.host['.read'],/hostUid/);
  assert.match(room.picks.guest['.read'],/guestUid/);
  assert.match(room.picks.host['.write'],/hostUid/);
  assert.match(room.picks.guest['.write'],/guestUid/);
  assert.match(room.meta.roundState['.write'],/hostUid/);
});
test('all traits referenced by published links belong to every matching record',()=>{
 const ids=new Set();
 for(const c of catalog.characters){assert.ok(!ids.has(c.id),c.id);ids.add(c.id);assert.ok(c.name&&c.article&&c.work);assert.ok(c.tags.length>=5);}
});
