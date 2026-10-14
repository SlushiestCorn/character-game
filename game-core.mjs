/* Pure game rules. This module has no Firebase or browser dependencies. */
export const HISTORY_SIZE = 70;
export function hash(str) {
  let h = 2166136261;
  for (let i=0; i<str.length; i++) { h ^= str.charCodeAt(i); h=Math.imul(h,16777619); }
  return h>>>0;
}
export function poolFor(catalog, traitId) {
  return catalog.characters.filter(c=>c.tags.includes(traitId));
}
export function storyKey(c) {
  // Historical/real people are not fictional characters from one shared franchise.
  return c.kind === 'real' ? 'person:'+c.id : c.work;
}
export function partition(c, seed) {
  // Split BY FRANCHISE/WORK, guaranteeing different works between opponents.
  return hash(seed+'|'+storyKey(c))%2;
}
export function viableLinks(catalog, seed) {
  const result=[];
  for (const link of catalog.links) {
    const pool=poolFor(catalog,link.id);
    if(pool.length<12 || pool.length>150) continue;
    const sides=[pool.filter(c=>partition(c,seed)===0),pool.filter(c=>partition(c,seed)===1)];
    const works=sides.map(a=>new Set(a.map(c=>storyKey(c))).size);
    if(sides.some(a=>a.length<5)||works.some(n=>n<3)) continue;
    const maxGroup=Math.max(...[...new Set(pool.map(x=>storyKey(x)))].map(w=>pool.filter(c=>storyKey(c)===w).length));
    if(maxGroup>pool.length*.35) continue;
    result.push({...link,actualCount:pool.length,worksBySide:works});
  }
  return result;
}
export function weightedLink(links, recent=[],random=Math.random) {
  if(!links.length) return null;
  const unused=links.filter(x=>!recent.includes(x.id));
  const options=unused.length ? unused : links;
  const weights=options.map(x=>{
    const pool=x.actualCount||x.pool;
    return 1/Math.sqrt(Math.max(1,pool/16));
  });
  const sum=weights.reduce((a,b)=>a+b,0);
  let cursor=random()*sum;
  for(let i=0;i<options.length;i++) if((cursor-=weights[i])<=0) return options[i];
  return options.at(-1);
}
export function candidatesForPick(catalog, linkId, seed, role, recentIds=[]) {
  // Host chooses GUEST'S identity from franchise-partition 0; guest chooses HOST'S from 1.
  const side=role==='host'?0:1;
  const pool=poolFor(catalog,linkId).filter(c=>partition(c,seed)===side);
  const fresh=pool.filter(c=>!recentIds.includes(c.id));
  return fresh.length?fresh:pool;
}
export function shuffle(array,rand=Math.random) {
  const a=array.slice();
  for(let i=a.length-1;i>0;i--) { const j=Math.floor(rand()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; }
  return a;
}
export function chooseSeedAndLink(catalog,recent=[],rand=Math.random) {
  // Try multiple deterministic partition seeds so less common links are not excluded unnecessarily.
  const offers=[];
  for(let i=0;i<5;i++) {
    const seed=cryptoSafeRandomSeed(rand);
    for(const link of viableLinks(catalog,seed)) offers.push({link,seed});
  }
  if(!offers.length) throw new Error('The catalogue has no sufficiently broad playable links.');
  const selected=weightedLink(offers.map(o=>({...o.link,unique:o.seed})),recent,rand);
  return {traitId:selected.id,seed:selected.unique};
}
export function cryptoSafeRandomSeed(random=Math.random) {
  // Caller supplies crypto-based random for production; Math.random is test fallback.
  return Math.floor(random()*4294967295).toString(36)+'-'+Math.floor(random()*4294967295).toString(36);
}
export function statusLabel(round,readyHost,readyGuest) {
  if(!round) return 'Waiting for the first round';
  if(readyHost!==round||readyGuest!==round) return 'Finding character images';
  return 'Ready to guess';
}
