const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const html=fs.readFileSync(path.join(__dirname,'pet-reactive-menus.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
assert(Buffer.byteLength(html)<1000000);
assert(!/<!doctype|<html|<head>|<body/i.test(html));
assert(!/FOX_IDLE|FOX_FRAMES|pm-y.*-6px|data-keyboard/.test(html));
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(x=>x[1]);
assert.equal(ids.length,new Set(ids).size);
for(const [,id] of html.matchAll(/(?:for|aria-controls)="([^"]+)"/g))assert(ids.includes(id));
const sprites=JSON.parse(html.match(/id="pm-sprites">([\s\S]*?)<\/script>/)[1]);
for(const [kind,frames] of Object.entries(sprites)){
  const originals=fs.readdirSync(path.join(__dirname,'../../assets/sprites/fox',kind)).filter(x=>/^frame_\d+\.png$/.test(x)).sort((a,b)=>Number(a.match(/\d+/)[0])-Number(b.match(/\d+/)[0]));
  assert.equal(frames.length,originals.length);
  frames.forEach((data,index)=>{
    const bytes=Buffer.from(data.split(',')[1],'base64');
    assert(bytes.equals(fs.readFileSync(path.join(__dirname,'../../assets/sprites/fox',kind,originals[index]))));
    if(kind==='idle'){assert.equal(bytes.readUInt32BE(16),46);assert.equal(bytes.readUInt32BE(20),37);}
  });
}
function node(){
  const events={},attrs={},styles={};
  return {hidden:false,dataset:{},textContent:'',value:'panel',src:'',clientWidth:320,clientHeight:214,
    styles,style:{setProperty:(k,v)=>styles[k]=v},attrs,setAttribute:(k,v)=>attrs[k]=v,
    addEventListener:(k,fn)=>events[k]=fn,fire:(k,e={})=>events[k]?.({preventDefault(){},...e}),
    getBoundingClientRect:()=>({left:0,top:0}),focus(){this.focused=true;}};
}
const map={};
for(const key of ['.pm-app','.pm-arena','.pm-pet','.pm-actions','.pm-global','#pm-style','.pm-status','[data-main]','[data-open]','[data-pause]','.pm-ball','.pm-heart','[data-close]','[data-action=sleep] span','[data-action=follow]','[data-action=follow] span'])map[key]=node();
const image=node();map['.pm-pet'].querySelector=()=>image;
let imageWrites=0,imageSource='';
Object.defineProperty(image,'src',{get:()=>imageSource,set:value=>{imageSource=value;imageWrites++;}});
const pauseText=node();map['[data-pause]'].querySelector=()=>pauseText;
const actions=['pet','ball','sleep','follow','settings','more'].map(key=>{const n=key==='follow'?map['[data-action=follow]']:node();n.dataset.action=key;return n;});
const root={querySelector:key=>{assert(map[key],key);return map[key];},querySelectorAll:()=>actions,addEventListener:()=>{}};
const docEvents={};
const doc={hidden:false,getElementById:key=>key===ids[0]?root:{textContent:JSON.stringify(sprites)},addEventListener:(key,fn)=>docEvents[key]=fn};
let now=1000,id=0,resize;
const frames=new Map();
const timers=new Map();
const context={document:doc,window:{addEventListener(){}},performance:{now:()=>now},requestAnimationFrame:fn=>{frames.set(++id,fn);return id;},cancelAnimationFrame:key=>frames.delete(key),setTimeout:fn=>{timers.set(++id,fn);return id;},clearTimeout:key=>timers.delete(key),ResizeObserver:class{constructor(fn){resize=fn;}observe(){}},Tweak:class{constructor(options){this.options=options;}addSlider(state,key){state[key]=18;this.options.onChange();}}};
vm.runInNewContext(script,context);
const pet=map['.pm-pet'],arena=map['.pm-arena'];
const x=()=>parseFloat(pet.styles['--pm-x']);
function frame(delta=33){now+=delta;const [key,fn]=frames.entries().next().value||[];if(fn){frames.delete(key);fn(now);}}
function move(px,py=127){now+=210;arena.fire('pointermove',{clientX:px,clientY:py});}
assert.equal(frames.size,0,'no animation on load');
pet.fire('click');assert.equal(frames.size,1,'first direct pet click activates the idle tail');
assert.equal(map['.pm-app'].styles['--pm-radius'],'18px');
map['#pm-style'].value='ring';map['#pm-style'].fire('change');
assert.equal(map['.pm-actions'].dataset.layout,'ring');
assert.equal(image.src,sprites.idle[0]);
const writesBeforeIdle=imageWrites;
for(let n=0;n<7;n++)frame(33);
frame(32);assert.equal(image.src,sprites.idle[0],'idle frame stays until 264ms');
assert.equal(imageWrites,writesBeforeIdle,'unchanged frames do not reassign PNG data');
frame(1);assert.equal(image.src,sprites.idle[1],'original idle advances at 264ms');
map['[data-close]'].fire('click');
assert.equal(image.src,sprites.idle[1],'closing menu preserves idle phase');
assert(map['.pm-actions'].hidden&&map['.pm-global'].hidden);
move(230);move(240);const before=x();frame();assert(x()>before,'real chase displacement');
assert.equal(image.styles['--pm-flip'],'1');
for(let n=0;n<30;n++)frame();
assert(sprites.idle.includes(image.src),'bounded one-shot movement finishes in idle');
const resting=x();for(let n=0;n<12;n++)frame();assert.equal(x(),resting,'idle tail does not move the pet');
move(x()+46+35);move(x()+46+100);const resumeStart=x();frame();assert(x()>resumeStart,'dead-zone cancellation keeps the chase encounter');
for(let n=0;n<30;n++)frame();
const idleBeforeMenu=image.src;map['[data-main]'].fire('click');assert.equal(image.src,idleBeforeMenu,'menu keeps idle phase');
const menuX=x();for(let n=0;n<8;n++)frame();assert.equal(x(),menuX);assert.notEqual(image.src,idleBeforeMenu,'tail continues with menu open');
map['[data-close]'].fire('click');
arena.fire('pointerleave');
const center=x()+46;move(center+65);move(center+75);const fleeStart=x();frame();assert(x()<fleeStart,'next encounter flees');
assert.equal(image.styles['--pm-flip'],'-1');
const boundedStart=x();frame(200);assert(Math.abs(x()-boundedStart)<=7.6,'dt is bounded after delayed frames');
map['[data-pause]'].fire('click');const paused=x();move(200);move(210);frame();assert.equal(x(),paused);assert.equal(frames.size,0);
map['[data-pause]'].fire('click');
actions.find(x=>x.dataset.action==='sleep').fire('click');assert(sprites.lie.includes(image.src));
move(220);move(230);assert.equal(frames.size,0,'sleep blocks cursor');
actions.find(x=>x.dataset.action==='sleep').fire('click');
actions.find(x=>x.dataset.action==='follow').fire('click');move(310);move(305);frame();
assert.equal(map['[data-action=follow]'].attrs['aria-pressed'],'true');
map['[data-main]'].fire('click');const menuStop=x();frame();assert.equal(x(),menuStop,'open menu stops movement');assert.equal(frames.size,1,'tail stays active in menu');
map['#pm-style'].value='panel';map['#pm-style'].fire('change');assert.equal(map['.pm-actions'].dataset.layout,'panel');
arena.clientWidth=120;resize();assert(x()<=28,'resize clamps to arena');
doc.hidden=true;docEvents.visibilitychange();assert.equal(frames.size,0,'hidden document stops all animation');
doc.hidden=false;docEvents.visibilitychange();assert.equal(frames.size,1,'visible document resumes only after activation');
console.log('PASS: fragment/IDs, original idle/walk/run/lie PNG bytes, idle 5x264ms cadence/phase, style picker, bounded chase/flee and stable encounter, facing, dt, pause/sleep/follow/menu/resize/hidden guards; no animation on load or keyboard bob.');
const previewPath=path.join(__dirname,'menu-preview.html');
if(fs.existsSync(previewPath)){
  const preview=fs.readFileSync(previewPath,'utf8');
  assert(/<!doctype html>/i.test(preview));
  const inner=preview;
  assert(inner.includes('pet-menu-motion-20261103'));
  assert(inner.replace(/\r\n/g,'\n').includes(script.replace(/\r\n/g,'\n')),'export must contain the current script');
  assert(!/<script[^>]+src=|<link[^>]+href=|<iframe|data-lucide=|https?:\/\//i.test(inner),'offline preview has no remote assets or frame');
  assert(inner.includes("connect-src 'none'"));
  assert(inner.includes('source-sha256:'+require('node:crypto').createHash('sha256').update(html).digest('hex')));
  let count=0;for(const match of inner.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)){if(/application\/json|\bsrc=/.test(match[1]))continue;new vm.Script(match[2]);count++;}
  assert(count===2);console.log('PASS: offline standalone export, local SVG icons, source hash, deny-network CSP, state fallback, '+count+' inline script syntax checks.');
}
console.log('No real browser/layout QA was available.');
