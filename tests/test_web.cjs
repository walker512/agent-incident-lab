// Synthetic UI contract tests. No browser, network, or private logs.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(){this.style={};this.children=[];this.hidden=false;this.value='all';this.classList={add(){},toggle(){}};}
 append(...nodes){this.children.push(...nodes);} replaceChildren(...nodes){this.children=nodes;}
 get firstChild(){return this.children[0];} setAttribute(){} addEventListener(){} scrollIntoView(){} focus(){}
 showModal(){this.open=true;} close(){this.open=false;} click(){return this.onclick?.();}
}
const elements=new Map(),get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const context=vm.createContext({document:{getElementById:get,createElement:()=>new Element()},Node:Element,window:{addEventListener(){}},Blob,setTimeout,URL,console});
vm.runInContext(fs.readFileSync('web/app.js','utf8'),context);
const run=code=>vm.runInContext(code,context);
run(`slots.A.report={status:'trusted',format:'claude',lines:{total:2,recognized:2,unknown:0,malformed:0},quality:{coverage:1,gate:false},metrics:{failedTools:1},source:{},findings:[{code:'tool_failed',message:'Explicit failure',lines:[1,2],nextStep:'Inspect locally'}],calls:[{name:'Bash',line:1,resultLine:2,status:'failed'}],ledger:[{line:1,status:'recognized',kind:'assistant'},{line:2,status:'recognized',kind:'user'}]};render();`);
assert.equal(get('headline').textContent,'1 explicit tool failure observed.');
assert.equal(get('status').textContent,'coverage-complete');
run('focusFinding(slots.A.report.findings[0])');
assert.equal(get('focus-panel').hidden,false);
assert.match(get('focus-summary').textContent,/1, 2/);
assert.match(get('focus-scope').textContent,/all 1 finding/);
run('invalidate()');assert.equal(get('focus-panel').hidden,true);
run(`renderChecks('preview-cards',{checks:{transcriptHash:'matched',privacy:'not-verified'}})`);
assert.equal(get('preview-cards').children.length,8);
assert.equal(get('preview-cards').children[7].children[1].textContent,'not-verified');
run(`bundleText='{}';`);
context.fetch=async()=>({ok:true,json:async()=>({bundleChecksPassed:true,checks:{privacy:'not-verified'},warnings:[]})});
(async()=>{
 await get('verify-preview').click();
 assert.match(get('preview-verdict').textContent,/privacy are NOT verified/);
 assert.equal(get('preview-details').hidden,false);
 let release;context.fetch=()=>new Promise(resolve=>{release=resolve;});
 const pending=get('verify-preview').click();run('closeDialog()');
 release({ok:true,json:async()=>({bundleChecksPassed:true,checks:{}})});await pending;
 assert.match(get('preview-verdict').textContent,/Re-run the parser/);
 assert.equal(get('preview-cards').children.length,0);
 console.log('UI contracts passed: failure/coverage separation, evidence focus, check cards, actual verification, stale-response guard.');
})().catch(error=>{console.error(error);process.exitCode=1;});
