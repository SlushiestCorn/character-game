import {firebaseConfig} from './firebase-config.js';
import {poolFor,viableLinks,weightedLink,candidatesForPick,chooseSeedAndLink,shuffle,statusLabel} from './game-core.mjs';

const $=id=>document.getElementById(id);
const s={catalog:null, firebase:null, auth:null,db:null,uid:null,roomId:'',role:'',meta:null,pick:null,pickBusyRound:0,unsub:[],mode:'lobby',demoRound:0,demoBusy:false,nextBusy:false,loaded:false};
const charsById=new Map();
const configReady=Boolean(firebaseConfig.apiKey&&firebaseConfig.databaseURL&&firebaseConfig.projectId);
const lazyImport=async()=>{
  if(s.firebase)return s.firebase;
  const [{initializeApp,getApps,getApp},{getAuth,signInAnonymously,onAuthStateChanged},{getDatabase,ref,set,get,onValue,runTransaction}] = await Promise.all([
    import('https://www.gstatic.com/firebasejs/12.4.0/firebase-app.js'),
    import('https://www.gstatic.com/firebasejs/12.4.0/firebase-auth.js'),
    import('https://www.gstatic.com/firebasejs/12.4.0/firebase-database.js')]);
  const app=getApps().length?getApp():initializeApp(firebaseConfig);
  s.firebase={ref,set,get,onValue,runTransaction,signInAnonymously,onAuthStateChanged};s.auth=getAuth(app);s.db=getDatabase(app);
  return s.firebase;
};

async function initAuth(){
  if(!configReady)throw Error('Firebase has not been configured. See the README for the free setup steps. The one-device preview works immediately.');
  const fb=await lazyImport();
  if(s.auth.currentUser){s.uid=s.auth.currentUser.uid;return;}
  const user=await new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>{off();reject(Error('Could not connect to Firebase Authentication.'));},15000);
    const off=fb.onAuthStateChanged(s.auth,async user=>{
      clearTimeout(timeout);off();
      if(user) resolve(user);
      else {try{const result=await fb.signInAnonymously(s.auth);resolve(result.user);}catch(e){reject(e);}}
    },reject);
  });
  s.uid=user.uid;
  return fb;
}
function alertUser(message,kind=''){const el=$('notice');el.hidden=false;el.textContent=message;el.className='notice '+kind;clearTimeout(alertUser.timer);alertUser.timer=setTimeout(()=>el.hidden=true,11000);}
function setBusy(btn,busy,label){btn.disabled=busy;if(busy){btn.dataset.original=btn.textContent;btn.textContent=label;}else if(btn.dataset.original){btn.textContent=btn.dataset.original;delete btn.dataset.original;}}
function screen(name){s.mode=name;for(const id of ['lobby','room','demo'])$(id).hidden=id!==name;window.scrollTo({top:0,behavior:'instant'});}
function randomInt(max){const bytes=new Uint32Array(1);crypto.getRandomValues(bytes);return Math.floor((bytes[0]/4294967296)*max);}
function rand(){return randomInt(1000000)/1000000;}
function randomCode(){const chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';return Array.from({length:6},()=>chars[randomInt(chars.length)]).join('');}
function nonce(){return randomCode()+Date.now().toString(36);}
function inviteURL(){const url=new URL(window.location.href);url.searchParams.set('room',s.roomId);url.hash='';return url.href;}
async function copyText(text){try{await navigator.clipboard.writeText(text);alertUser('Copied to clipboard.','success');}catch{window.prompt('Copy this link:',text);}}
function getSaved(key){try{return JSON.parse(localStorage.getItem(key)||'[]');}catch{return [];}}
function saveRecent(key,val,max=60){const list=getSaved(key).filter(x=>x!==val);list.unshift(val);localStorage.setItem(key,JSON.stringify(list.slice(0,max)));}
function setRoomHash(){const u=new URL(window.location.href);u.searchParams.set('room',s.roomId);history.replaceState({},'',u.href);}
function clearRoomHash(){const u=new URL(window.location.href);u.searchParams.delete('room');history.replaceState({},'',u.href);}
function teardown(){for(const un of s.unsub)try{un();}catch{}s.unsub=[];s.meta=null;s.pick=null;s.pickBusyRound=0;s.roomId='';s.role='';s.nextBusy=false;}
function roomRef(path=''){return s.firebase.ref(s.db,'rooms/'+s.roomId+(path?'/'+path:''));}
async function createRoom(){
  const btn=$('createBtn');setBusy(btn,true,'Connecting…');
  try{
    await initAuth();teardown();
    for(let tries=0;tries<7;tries++){
      s.roomId=randomCode();
      const exists=await s.firebase.get(roomRef('meta'));
      if(exists.exists())continue;
      await s.firebase.set(roomRef('meta'),{hostUid:s.uid,createdAt:Date.now(),roundState:{number:0,traitId:'',seed:''}});
      s.role='host';enterRoom();return;
    }
    throw Error('Could not find a free room code; please try again.');
  }catch(e){alertUser('Unable to create room: '+e.message,'error');}
  finally{setBusy(btn,false);}
}
async function joinRoom(input){
  const code=input.trim().toUpperCase().replace(/[^A-Z0-9]/g,'');
  if(code.length!==6){alertUser('Enter a 6-character room code.','error');return;}
  const btn=$('joinForm').querySelector('button');setBusy(btn,true,'Joining…');
  try{
    await initAuth();teardown();s.roomId=code;
    const snapshot=await s.firebase.get(roomRef('meta'));
    if(!snapshot.exists())throw Error('Room not found. Check the code with the host.');
    const meta=snapshot.val();
    if(meta.hostUid===s.uid)s.role='host';
    else if(meta.guestUid===s.uid)s.role='guest';
    else if(meta.guestUid)throw Error('This room already has two players.');
    else{
      await s.firebase.set(roomRef('meta/guestUid'),s.uid);
      s.role='guest';
    }
    enterRoom();
  }catch(e){alertUser('Unable to join: '+e.message,'error');}
  finally{setBusy(btn,false);}
}
function enterRoom(){
  screen('room');setRoomHash();
  $('roomCode').textContent=s.roomId;$('waitingCode').textContent=s.roomId;
  $('myRole').textContent=s.role==='host'?'Player 1':'Player 2';
  $('connectionStatus').textContent='Connected';$('connectionStatus').classList.remove('waiting');
  const metaUn=s.firebase.onValue(roomRef('meta'), snap=>{s.meta=snap.val();onMetaChange().catch(error=>alertUser(error.message,'error'));},error=>alertUser('Room connection failed: '+error.message,'error'));
  // CRITICAL: listen ONLY to the path belonging to THIS DEVICE.
  // Never read /rooms/<room>/picks or the other seat's private path.
  const pickUn=s.firebase.onValue(roomRef('picks/'+s.role),snap=>{s.pick=snap.val();renderGame();},error=>alertUser('Private card could not be loaded: '+error.message,'error'));
  s.unsub.push(metaUn,pickUn);
  renderGame();
}
async function onMetaChange(){
  const meta=s.meta;if(!meta||!s.role)return;
  if(s.role==='host' && meta.guestUid && meta.roundState?.number===0 && !s.nextBusy){await startNextRound();}
  if(s.role==='host' && meta.guestUid && meta.nextRequest && meta.roundState?.number>0 && meta.nextRequest.forRound===meta.roundState.number && !s.nextBusy){await startNextRound();}
  renderGame();
  if(meta.roundState?.number>0 && meta.guestUid)ensurePick(meta.roundState).catch(error=>alertUser('Could not assign a character: '+error.message,'error'));
}
async function startNextRound(){
  if(s.role!=='host'||!s.meta?.guestUid||s.nextBusy)return;
  s.nextBusy=true;
  const btn=$('nextRoundBtn');btn.disabled=true;
  try{
    const recent=getSaved('gtc-links-'+s.roomId);
    const next=chooseSeedAndLink(s.catalog,recent,rand);
    const current=s.meta.roundState.number;
    await s.firebase.set(roomRef('meta/roundState'),{number:current+1,traitId:next.traitId,seed:next.seed});
    saveRecent('gtc-links-'+s.roomId,next.traitId,35);
  }catch(e){alertUser('New round failed: '+e.message,'error');}
  finally{s.nextBusy=false;btn.disabled=false;}
}
async function requestNextRound(){
  if(!s.meta?.guestUid)return;
  if(!window.confirm('Replace both players’ characters and the shared clue with a new round?'))return;
  if(s.role==='host')await startNextRound();
  else{
    try{await s.firebase.set(roomRef('meta/nextRequest'),{forRound:s.meta.roundState.number,nonce:nonce()});alertUser('New round requested. It will begin when Player 1 is connected.','success');}
    catch(e){alertUser('Could not request a new round: '+e.message,'error');}
  }
}
function readablePick(p){return p?.round===s.meta?.roundState?.number ? charsById.get(p.characterId):null;}
async function ensurePick(roundState){
  const {number,traitId,seed}=roundState;
  if(s.pick?.round===number||s.pickBusyRound===number)return;
  if(!s.catalog.links.some(l=>l.id===traitId))return;
  s.pickBusyRound=number;renderGame();
  try{
    const key='gtc-chars-'+s.roomId+'-'+s.role;
    const options=shuffle(candidatesForPick(s.catalog,traitId,seed,s.role,getSaved(key)),rand);
    if(!options.length)throw Error('No candidates in this half of the pool.');
    let choice=null,info=null;
    // Try multiple works. Wikipedia may lack individual images for obscure characters.
    for(let i=0;i<Math.min(12,options.length);i+=4){
      const group=options.slice(i,i+4);
      const results=await Promise.all(group.map(c=>getImageFor(c)));
      const index=results.findIndex(Boolean);
      if(index>=0){choice=group[index];info=results[index];break;}
      if(s.meta?.roundState?.number!==number)return;
    }
    if(!choice){
      // Always return a name, even when remote sites have no usable picture.
      choice=options[0];info={url:'',source:wikipediaLink(choice.article)};
      alertUser('No verifiable image was found automatically. Use “Fix image” to supply a direct picture URL.','error');
    }
    if(s.meta?.roundState?.number!==number)return;
    await s.firebase.set(roomRef('picks/'+s.role),{round:number,characterId:choice.id,imageUrl:info.url,source:info.source});
    saveRecent(key,choice.id,100);
    await s.firebase.set(roomRef('meta/ready/'+s.role),number);
  }finally{if(s.pickBusyRound===number)s.pickBusyRound=0;renderGame();}
}
function wikipediaLink(title){return 'https://en.wikipedia.org/wiki/'+encodeURIComponent(title.replaceAll(' ','_'));}
async function imageIsValid(url){
  if(!url)return false;
  return new Promise(resolve=>{
    const img=new Image();let done=false;
    const t=setTimeout(()=>finish(false),5500);
    function finish(ok){if(done)return;done=true;clearTimeout(t);img.onload=img.onerror=null;resolve(ok);}
    img.onload=()=>finish(img.naturalWidth>70 && img.naturalHeight>70);
    img.onerror=()=>finish(false);
    img.src=url;
  });
}
const imageCache=new Map();
async function wikiImage(article){
  const api=new URL('https://en.wikipedia.org/w/api.php');
  for(const [k,v] of Object.entries({action:'query',format:'json',origin:'*',redirects:'1',prop:'pageimages',piprop:'thumbnail|name',pilicense:'any',pithumbsize:'800',titles:article}))api.searchParams.set(k,v);
  const response=await fetch(api,{signal:AbortSignal.timeout(7500)});
  if(!response.ok) return null;
  const data=await response.json();
  const page=Object.values(data.query?.pages??{})[0];
  if(!page||page.missing||!page.thumbnail?.source)return null;
  const url=page.thumbnail.source;
  const source=page.pageimage?'https://en.wikipedia.org/wiki/'+encodeURIComponent('File:'+page.pageimage.replace(/^File:/,'')):wikipediaLink(page.title);
  return await imageIsValid(url)?{url,source}:null;
}
async function getImageFor(character){
  const override=localStorage.getItem('gtc-img-'+character.id);
  if(override && await imageIsValid(override))return {url:override,source:override};
  if(character.imageUrl && await imageIsValid(character.imageUrl))return {url:character.imageUrl,source:character.imageSource||character.imageUrl};
  if(imageCache.has(character.article))return imageCache.get(character.article);
  let info=null;
  try{info=await wikiImage(character.article);}catch{/* Wikipedia or network may be unavailable. */}
  // Do not silently select an unrelated image from a character's franchise.
  imageCache.set(character.article,info);
  return info;
}
function renderGame(){
  if(s.mode!=='room')return;
  const meta=s.meta;const round=meta?.roundState?.number||0;const hasGuest=Boolean(meta?.guestUid);
  $('waiting').hidden=hasGuest;$('gameplay').hidden=!hasGuest;
  $('connectionStatus').textContent=hasGuest?'2 players connected':'Waiting for Player 2';
  $('connectionStatus').classList.toggle('waiting',!hasGuest);
  if(!hasGuest)return;
  const link=s.catalog?.links.find(l=>l.id===meta.roundState?.traitId);
  $('roundLabel').textContent='ROUND '+String(round).padStart(2,'0');
  $('clueText').textContent=link?.label||'Selecting a shared clue…';
  const c=readablePick(s.pick);
  $('characterName').textContent=c?.name||(round?'Assigning your opponent’s character…':'Preparing the first round…');
  $('characterWork').textContent=c?.work||' ';
  const image=c && s.pick?.imageUrl;
  const img=$('characterImage');
  if(image){
    if(img.dataset.url!==image){img.dataset.url=image;img.src=image;img.alt='Picture of '+c.name;}
    img.hidden=false;$('imageLoading').hidden=true;
  }else{
    img.hidden=true;img.removeAttribute('src');delete img.dataset.url;$('imageLoading').hidden=false;
    $('imageLoading').lastElementChild.textContent=c?'No automatic image — select “Fix image”':'Finding a suitable character…';
  }
  $('imageSource').href=(s.pick?.source||c&&wikipediaLink(c.article)||'#').startsWith('http')?(s.pick?.source||wikipediaLink(c.article)):'#';
  $('imageSource').hidden=!c;
  $('replaceImageBtn').disabled=!c;
  const bothReady=meta.ready?.host===round&&meta.ready?.guest===round;
  const currentTurn=meta.turn?.round===round?meta.turn.role:'host';
  const solved=meta.solved||{};
  $('player1Status').textContent=solved.host===round?'Guessed!':meta.ready?.host===round?(currentTurn==='host'?'Asking now':'Ready'):'Selecting…';
  $('player2Status').textContent=solved.guest===round?'Guessed!':meta.ready?.guest===round?(currentTurn==='guest'?'Asking now':'Ready'):'Selecting…';
  if(!bothReady){$('statusTitle').textContent='Setting up the round';$('statusDescription').textContent='Each phone is independently choosing a character for its opponent.';}
  else if(solved.host===round&&solved.guest===round){$('statusTitle').textContent='Round complete';$('statusDescription').textContent='Both players have guessed. Start another round when ready.';}
  else{$('statusTitle').textContent=(currentTurn==='host'?'Player 1':'Player 2')+' asks next';$('statusDescription').textContent='Ask a yes-or-no question aloud. The other player answers while looking at their screen.';}
  $('passTurnBtn').disabled=!bothReady;
  $('solvedBtn').disabled=!bothReady||solved[s.role]===round;
  $('solvedBtn').textContent=solved[s.role]===round?'✓ You marked your guess':'I guessed my character ✓';
  $('nextRoundBtn').disabled=!round||!hasGuest||s.nextBusy;
}
async function passTurn(){
  const round=s.meta?.roundState?.number||0;if(!round)return;
  const role=s.meta.turn?.round===round?s.meta.turn.role:'host';
  try{await s.firebase.set(roomRef('meta/turn'),{round,role:role==='host'?'guest':'host'});}catch(e){alertUser(e.message,'error');}
}
async function markSolved(){
  const round=s.meta?.roundState?.number;if(!round)return;
  try{await s.firebase.set(roomRef('meta/solved/'+s.role),round);}catch(e){alertUser(e.message,'error');}
}
function closeRoom(){teardown();clearRoomHash();screen('lobby');}
async function openImageDialog(){const c=readablePick(s.pick);if(!c)return;
  $('imageUrlInput').value=localStorage.getItem('gtc-img-'+c.id)||s.pick.imageUrl||'';
  $('findImageLink').href='https://www.google.com/search?tbm=isch&q='+encodeURIComponent(c.name+' '+c.work+' character');
  $('imageDialog').showModal();
}
async function saveImageOverride(event){event.preventDefault();const c=readablePick(s.pick);if(!c)return;
  const url=$('imageUrlInput').value.trim();
  let parsed;try{parsed=new URL(url);if(parsed.protocol!=='https:'&&parsed.protocol!=='http:')throw Error('URL must be HTTP or HTTPS');}catch{alertUser('Enter a valid direct image URL.','error');return;}
  if(!await imageIsValid(url)){alertUser('That address did not load as a picture. Try a direct image URL.','error');return;}
  localStorage.setItem('gtc-img-'+c.id,url);$('imageDialog').close();
  try{await s.firebase.set(roomRef('picks/'+s.role),{...s.pick,imageUrl:url,source:url});}
  catch(e){alertUser('The image was saved locally but could not be updated in the room: '+e.message,'error');}
}
async function resetImageOverride(){const c=readablePick(s.pick);if(!c)return;
  localStorage.removeItem('gtc-img-'+c.id);imageCache.delete(c.article);
  const image=await getImageFor(c);$('imageDialog').close();
  await s.firebase.set(roomRef('picks/'+s.role),{...s.pick,imageUrl:image?.url||'',source:image?.source||wikipediaLink(c.article)});
}
async function demoRound(){if(s.demoBusy)return;s.demoBusy=true;$('demoNextBtn').disabled=true;
  try{
    const {traitId,seed}=chooseSeedAndLink(s.catalog,getSaved('gtc-demo-links'),rand);
    const link=s.catalog.links.find(l=>l.id===traitId);
    $('demoClue').textContent=link.label;
    saveRecent('gtc-demo-links',traitId,28);
    const a=shuffle(candidatesForPick(s.catalog,traitId,seed,'host',getSaved('gtc-demo-chars')),rand);
    const b=shuffle(candidatesForPick(s.catalog,traitId,seed,'guest',getSaved('gtc-demo-chars')),rand);
    const find=async(options)=>{for(let i=0;i<Math.min(12,options.length);i+=4){const group=options.slice(i,i+4);const results=await Promise.all(group.map(c=>getImageFor(c)));const j=results.findIndex(Boolean);if(j>=0)return [group[j],results[j].url];}return [options[0],''];};
    // Mirrors the two device assignments, but deliberately displays both for testing.
    const [player1,player2]=await Promise.all([find(a),find(b)]);
    [['1',player1],['2',player2]].forEach(([slot,[c,url]])=>{
      $('demoName'+slot).textContent=c.name;
      $('demoWork'+slot).textContent=c.work;
      const img=$('demoImage'+slot);img.src=url||'';img.alt=url?'Picture of '+c.name:'No image available';
      saveRecent('gtc-demo-chars',c.id,100);
    });
  }catch(e){alertUser('Preview failed: '+e.message,'error');}
  finally{s.demoBusy=false;$('demoNextBtn').disabled=false;}
}
$('characterImage').addEventListener('error',()=>{
  $('characterImage').hidden=true;$('imageLoading').hidden=false;
  $('imageLoading').lastElementChild.textContent='Image blocked by its source — use “Fix image”.';
});
$('createBtn').onclick=createRoom;
$('joinForm').addEventListener('submit',event=>{event.preventDefault();joinRoom($('joinCode').value);});
$('copyCodeBtn').onclick=()=>copyText(inviteURL());$('inviteBtn').onclick=()=>copyText(inviteURL());
$('leaveBtn').onclick=closeRoom;
$('nextRoundBtn').onclick=requestNextRound;
$('passTurnBtn').onclick=passTurn;
$('solvedBtn').onclick=markSolved;
$('replaceImageBtn').onclick=openImageDialog;
$('imageForm').addEventListener('submit',saveImageOverride);
$('resetImageBtn').onclick=()=>resetImageOverride().catch(e=>alertUser(e.message,'error'));
$('demoBtn').onclick=()=>{screen('demo');demoRound();};$('exitDemoBtn').onclick=()=>screen('lobby');$('demoNextBtn').onclick=demoRound;
(async function boot(){
  try{
    const response=await fetch('./data/catalog.json');if(!response.ok)throw Error('catalog.json could not be opened');
    s.catalog=await response.json();s.loaded=true;
    for(const c of s.catalog.characters)charsById.set(c.id,c);
    $('catalogueCount').textContent=s.catalog.characters.length+' characters · '+s.catalog.links.length+' playable clues · no AI charges';
    if(!configReady){$('configHint').textContent='Multiplayer setup is not yet configured. The preview works now; see README.md to activate two-phone play.';}
    else {$('configHint').textContent='Multiplayer is configured. Create a room or join a friend.';}
    const code=new URLSearchParams(window.location.search).get('room');
    if(code){$('joinCode').value=code.toUpperCase();if(configReady)await joinRoom(code);}
  }catch(e){alertUser('Could not start the game: '+e.message,'error');}
})();
