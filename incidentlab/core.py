"""Deterministic native transcript inspection. Never executes transcript contents."""
from __future__ import annotations
import hashlib
import json
from collections import Counter
from typing import Any

VERSION = '0.1.0'
MAX_BYTES = 16 * 1024 * 1024
MAX_LINES = 100_000
MAX_LINE = 2 * 1024 * 1024
FORMATS = ('auto', 'codex-exec', 'codex-session', 'claude')
EXEC_TYPES = {'thread.started','turn.started','turn.completed','turn.failed','error','item.started','item.updated','item.completed'}
SESSION_TYPES = {'session_meta','turn_context','response_item','event_msg','compacted'}
CLAUDE_TYPES = {'assistant','user','system','result','summary','file-history-snapshot','queue-operation','progress','last-prompt','pr-link','custom-title','agent-name','agent-color'}
TOOLS = {'command_execution','mcp_tool_call','web_search','file_change'}
SAFE_NAMES = {'shell','shell_command','exec_command','write_stdin','apply_patch','read_file','list_dir','grep_files','update_plan','request_user_input','view_image','Bash','Read','Write','Edit','MultiEdit','Glob','Grep','Task','TodoWrite','WebFetch','WebSearch','command_execution','mcp_tool_call','web_search','file_change'}

NEXT_STEPS = {
 'tool_failed': 'Open the call and result source lines locally. Check whether this is an expected failure, a cancelled sibling, or the first failing command. Export the tool_failed slice for parser triage; restore commands/environment privately to investigate execution.',
 'missing_result': 'Confirm the producer has finished and the file was copied completely. If it is final, inspect shutdown/abort records near the last call. Do not mark a missing result successful.',
 'unknown_outcome': 'Inspect the original result privately. A native output string is not a reliable structured success flag. Include producer version when requesting adapter support.',
 'orphan_result': 'Check whether an earlier file segment contains the call. Import one complete session, not a tail or merged set. If still orphaned, preserve the result line as evidence.',
 'duplicate_call_id': 'Check for concatenated sessions or repeated stream chunks. Split by original session before correlation; do not deduplicate blindly.',
 'duplicate_result': 'Check for repeated chunks or multiple sessions sharing IDs. Preserve both occurrences; choosing the last result can hide a failure.',
 'conflicting_tool_name': 'Check whether two sessions were concatenated. The same ID cannot safely identify different tools in this parser.',
 'result_before_call': 'Check whether the file was reordered or assembled from parallel streams. Source order is not proof of wall-clock order.',
 'mixed_formats': 'Split the input by producer and native format. Codex exec stdout is different from a Codex saved rollout. Do not concatenate them.',
 'unknown_format': 'Confirm this is native JSONL, not a JSON array, OTLP export, Codex TUI capture, or plain console output. Select the matching parser explicitly to diagnose a mismatch.',
 'unrecognized_records': 'Use the ledger unknown filter, note the producer version and record kind, and prepare a structural case. Counts are lower bounds until the adapter understands these records.',
 'malformed_records': 'Use the malformed ledger filter. Check incomplete copy, truncated last line, duplicate keys, wrong role, and missing required fields. Do not silently drop bad rows.',
 'agent_error': 'Inspect this source line locally for the actual runtime error or user interruption. The hidden prose is not exported; this code alone does not identify a root cause.',
 'no_tool_activity': 'A conversation-only or metadata-only file can be valid but says nothing about tool execution. Verify you selected the intended session and format.'
}

class InputError(ValueError): pass

def strict_loads(s):
    def pairs(items):
        out = {}
        for k,v in items:
            if k in out: raise ValueError('duplicate JSON key')
            out[k] = v
        return out
    return json.loads(s, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non-finite JSON number')))

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'))

def digest(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()

def valid_id(value): return isinstance(value, str) and 0 < len(value) <= 4096

def records(text):
    if not isinstance(text, str): raise InputError('Transcript must be text.')
    try: size = len(text.encode('utf-8'))
    except UnicodeError: raise InputError('Transcript must be valid UTF-8.')
    if size > MAX_BYTES: raise InputError('Transcript exceeds 16 MiB limit.')
    lines = text.splitlines()
    if len(lines) > MAX_LINES: raise InputError('Transcript exceeds 100,000 lines.')
    out=[]
    for n,line in enumerate(lines,1):
        if not line.strip(): continue
        if len(line.encode('utf-8')) > MAX_LINE:
            out.append((n,None,'Line exceeds 2 MiB limit.')); continue
        try:
            value = strict_loads(line)
            if not isinstance(value,dict): raise ValueError('not an object')
            out.append((n,value,None))
        except (ValueError,RecursionError): out.append((n,None,'Invalid JSON object, duplicate key, or excessive nesting.'))
    if not out: raise InputError('Transcript is empty. Select a JSONL session file.')
    return out

def family(row):
    typ=row.get('type')
    if not isinstance(typ,str): return None
    if typ in EXEC_TYPES: return 'codex-exec'
    if typ in SESSION_TYPES: return 'codex-session'
    if typ in CLAUDE_TYPES: return 'claude'
    return None

def analyze(text: str, format: str='auto') -> dict:
    if format not in FORMATS: raise InputError('Unknown parser format.')
    rows=records(text)
    detected=Counter(family(r) for _,r,e in rows if r and family(r))
    selected=format
    if format=='auto': selected=next(iter(detected)) if len(detected)==1 else 'mixed' if detected else 'unknown'
    ledger=[]; calls=[]; findings=[]; by_id={}; outputs=[]
    ids={}; names={}
    def alias(value, table, prefix):
        if value not in table: table[value]=f'{prefix}{len(table)+1}'
        return table[value]
    def finding(code,message,lines,severity='warning'):
        findings.append(dict(code=code,message=message,lines=lines,severity=severity,nextStep=NEXT_STEPS.get(code,'Review the original source locally before drawing conclusions.')))
    def call(key,name,n,pointer,status='pending',result=False,update=False):
        if not valid_id(key) or not isinstance(name,str) or not name:
            raise ValueError('Tool call requires a string ID and name.')
        shown=name if name in SAFE_NAMES else alias(name,names,'tool-')
        if key in by_id:
            c=by_id[key]
            if not update:
                finding('duplicate_call_id','Tool call ID appears more than once; correlation is ambiguous.',[c['line'],n],'error')
                c['status']='unknown'; c['_ambiguous']=True
            elif c['name']!=shown:
                finding('conflicting_tool_name','Tool name changes for the same ID.',[c['line'],n],'error'); c['_ambiguous']=True;c['status']='unknown'
            elif result and c['resultLine'] is not None:
                finding('duplicate_result','Multiple completions refer to the same call; outcome is ambiguous.',[c['resultLine'],n],'error')
                c['_ambiguous']=True;c['status']='unknown'
            elif result and not c.get('_ambiguous'):
                c['status']=status;c['resultLine']=n
                c['evidence'].append(dict(line=n,pointer=pointer,code='tool_completion'))
            return
        c=dict(id=alias(key,ids,'call-'),name=shown,line=n,resultLine=n if result else None,status=status,evidence=[dict(line=n,pointer=pointer,code='tool_completion' if result else 'tool_call')],_key=key)
        calls.append(c);by_id[key]=c
    def output(key,n,pointer,status):
        if not valid_id(key): raise ValueError('Tool result requires a string correlation ID.')
        outputs.append((key,n,pointer,status))
    def exec_row(r,n):
        typ=r['type']
        if typ.startswith('item.'):
            item=r.get('item')
            if not isinstance(item,dict) or not isinstance(item.get('type'),str): raise ValueError('Missing item.type object discriminator.')
            it=item['type']
            if it in TOOLS:
                state=item.get('status')
                done=typ=='item.completed'
                status='pending'
                if done:
                    if state in ('failed','declined'): status='failed'
                    elif it=='command_execution':
                        ec=item.get('exit_code')
                        if type(ec) is int: status='success' if ec==0 else 'failed'
                        else: status='unknown'
                    elif state=='completed': status='success'
                    else: status='unknown'
                call(item.get('id'),it,n,'/item',status,done,typ!='item.started')
            elif it not in {'agent_message','reasoning','todo_list'}: return False,'Unsupported item.type.'
            return True,None
        if typ in {'turn.failed','error'}: finding('agent_error','Agent runtime reports an error. Content intentionally omitted.',[n],'error')
        return True,None
    def session_row(r,n):
        typ=r['type'];p=r.get('payload')
        if not isinstance(p,dict): raise ValueError('Missing payload object.')
        if typ=='response_item':
            pt=p.get('type')
            if pt in {'function_call','custom_tool_call'}: call(p.get('call_id'),p.get('name'),n,'/payload')
            elif pt in {'function_call_output','custom_tool_call_output'}:
                # Native outputs are commonly opaque strings: completion is known, success is not.
                out=p.get('output'); status='unknown'
                if isinstance(out,dict) and type(out.get('exit_code')) is int: status='success' if out['exit_code']==0 else 'failed'
                output(p.get('call_id'),n,'/payload/output',status)
            elif pt not in {'message','reasoning','web_search_call','local_shell_call','compaction','image_generation_call'}: return False,'Unsupported response_item.payload.type.'
            elif pt in {'web_search_call','local_shell_call','image_generation_call'}: return False,'Native server-side tool variant is not yet modeled.'
        elif typ=='event_msg':
            pt=p.get('type')
            if pt not in {'user_message','agent_message','agent_reasoning','token_count','task_started','task_complete','turn_aborted','context_compacted','thread_rolled_back','error','warning','item_started','item_completed','raw_response_item','exec_command_begin','exec_command_end','mcp_tool_call_begin','mcp_tool_call_end','patch_apply_begin','patch_apply_end','plan_update','shutdown_complete'}: return False,'Unsupported event_msg.payload.type.'
            if pt in {'error','turn_aborted'}: finding('agent_error','Agent runtime reports an error or aborted turn.',[n],'error')
            # Side-channel tool lifecycle is not authoritative: do not double-count response_item calls.
        return True,None
    def claude_row(r,n):
        typ=r['type']
        if typ in {'assistant','user'}:
            msg=r.get('message')
            if not isinstance(msg,dict): raise ValueError('Missing message object.')
            if 'role' in msg and msg['role']!=typ: raise ValueError('Message role disagrees with record type.')
            content=msg.get('content')
            if isinstance(content,str): return True,None
            if not isinstance(content,list): raise ValueError('Missing message.content array or string.')
            known=True
            for i,b in enumerate(content):
                ptr=f'/message/content/{i}'
                if not isinstance(b,dict): raise ValueError('Content block must be an object.')
                bt=b.get('type')
                if bt=='tool_use':
                    if typ!='assistant': raise ValueError('tool_use is only supported in assistant messages.')
                    if not isinstance(b.get('input'),dict): raise ValueError('tool_use requires an input object.')
                    call(b.get('id'),b.get('name'),n,ptr)
                elif bt=='tool_result':
                    if typ!='user': raise ValueError('tool_result is only supported in user messages.')
                    if not isinstance(b.get('content'),(str,list)): raise ValueError('tool_result requires string or array content.')
                    err=b.get('is_error',False)
                    if type(err) is not bool: raise ValueError('is_error must be boolean.')
                    output(b.get('tool_use_id'),n,ptr,'failed' if err else 'success')
                elif bt not in {'text','thinking','redacted_thinking','image','document','server_tool_use','web_search_tool_result','tool_reference'}: known=False
                elif bt in {'server_tool_use','web_search_tool_result'}: known=False
            return known,None if known else 'Unsupported content block; supported blocks on this line were inspected.'
        if typ=='result' and r.get('is_error') is True: finding('agent_error','Agent result reports an error.',[n],'error')
        return True,None
    if selected=='mixed': finding('mixed_formats','Multiple native formats detected. Split sessions before trusting metrics.',[],'error')
    if selected=='unknown': finding('unknown_format','No supported native event discriminator found. No zero-success inference is made.',[],'error')
    for n,r,error in rows:
        if error:
            ledger.append(dict(line=n,kind='invalid',status='malformed',pointer='/',reason=error));continue
        typ=r.get('type');kind=typ if isinstance(typ,str) and typ in EXEC_TYPES|SESSION_TYPES|CLAUDE_TYPES else 'unrecognized'
        entry=dict(line=n,kind=kind,status='unknown',pointer='/')
        if selected not in FORMATS[1:] or family(r)!=selected:
            entry['reason']='Event does not match the selected native parser.'
        else:
            try:
                ok,reason={'codex-exec':exec_row,'codex-session':session_row,'claude':claude_row}[selected](r,n)
                entry['status']='recognized' if ok else 'unknown'
                if reason: entry['reason']=reason
            except (ValueError,TypeError,KeyError,RecursionError) as exc:
                entry['status']='malformed'; entry['reason']=str(exc) if isinstance(exc,ValueError) else 'Malformed native record.'
        ledger.append(entry)
    result_seen={}
    for key,n,ptr,status in outputs:
        if key in result_seen:
            finding('duplicate_result','Multiple results refer to the same call; outcome is ambiguous.',[result_seen[key],n],'error')
            if key in by_id: by_id[key]['status']='unknown';by_id[key]['_ambiguous']=True
            continue
        result_seen[key]=n
        if key not in by_id:
            finding('orphan_result','Tool result has no matching call in this file.',[n]);continue
        c=by_id[key]
        if n<c['line']: finding('result_before_call','Result precedes its call in file order.',[n,c['line']])
        c['resultLine']=n
        if not c.get('_ambiguous'): c['status']=status
        c['evidence'].append(dict(line=n,pointer=ptr,code='tool_result'))
    for c in calls:
        if c['status']=='failed': finding('tool_failed','Tool reports an explicit failure.',[c['line'],c['resultLine']],'error')
        elif c['status']=='pending': finding('missing_result','No completion was found. A truncated or still-running session is possible.',[c['line']])
        elif c['status']=='unknown': finding('unknown_outcome','Completion exists or correlation is ambiguous, but success cannot be established.',[c['line']])
        c.pop('_key',None);c.pop('_ambiguous',None)
    if not calls and selected in FORMATS[1:]: finding('no_tool_activity','No supported tool calls found. This is not evidence of a successful agent run.',[])
    counts=Counter(e['status'] for e in ledger)
    if counts['unknown']: finding('unrecognized_records','Some records or content blocks were not understood; metrics are lower bounds.',[e['line'] for e in ledger if e['status']=='unknown'],'error')
    if counts['malformed']: finding('malformed_records','Malformed records prevent a complete interpretation.',[e['line'] for e in ledger if e['status']=='malformed'],'error')
    status='unsupported' if selected not in FORMATS[1:] or counts['recognized']==0 else 'partial' if counts['unknown'] or counts['malformed'] else 'trusted'
    # Trusted means parser coverage only, not successful task completion.
    metrics=None if status=='unsupported' else dict(toolCalls=len(calls),toolResults=sum(c['resultLine'] is not None for c in calls),failedTools=sum(c['status']=='failed' for c in calls),pendingTools=sum(c['status']=='pending' for c in calls),unknownOutcomes=sum(c['status']=='unknown' for c in calls))
    return dict(schemaVersion=1,parserVersion=VERSION,format=selected,status=status,source=dict(sha256=digest(text),bytes=len(text.encode('utf-8'))),lines=dict(total=len(ledger),recognized=counts['recognized'],unknown=counts['unknown'],malformed=counts['malformed']),metrics=metrics,quality=dict(coverage=round(counts['recognized']/len(ledger),4),gate=status=='trusted' and not findings),ledger=ledger,calls=calls,findings=findings)

def signature(report):
    return {k:report[k] for k in ('format','status','lines','metrics','quality')} | {'findings':dict(sorted(Counter(f['code'] for f in report['findings']).items()))}

def compare(before,after):
    for r in (before,after):
        if not isinstance(r,dict) or r.get('schemaVersion')!=1: raise InputError('Expected an Incident Lab v1 report.')
    compatible=before.get('format')==after.get('format') and before.get('status')=='trusted' and after.get('status')=='trusted' and before.get('parserVersion')==after.get('parserVersion')
    deltas={}
    if isinstance(before.get('metrics'),dict) and isinstance(after.get('metrics'),dict):
        for k in ('toolCalls','toolResults','failedTools','pendingTools','unknownOutcomes'):
            a=before['metrics'].get(k);b=after['metrics'].get(k)
            if type(a) is not int or type(b) is not int: raise InputError('Invalid report metrics.')
            deltas[k]=dict(before=a,after=b,delta=b-a)
    return dict(comparable=compatible,verdict='comparable-imports' if compatible else 'inconclusive',note='Imported observations only. Different tasks, prompts, models, or truncation can explain changes; this is not a controlled agent experiment.',deltas=deltas,beforeQuality=before.get('quality'),afterQuality=after.get('quality'))

# This is an allowlist projection, not a promise that regex can redact arbitrary prose.
# No input string is copied except closed enumerations. Correlation IDs are renumbered.
def project(text):
    ids={}; names={}
    def ident(value):
        if not valid_id(value): return None
        if value not in ids: ids[value]=f'id-{len(ids)+1}'
        return ids[value]
    def name(value):
        if not isinstance(value,str) or not value: return None
        if value in SAFE_NAMES: return value
        if value not in names: names[value]=f'private-tool-{len(names)+1}'
        return names[value]
    def enum(value,allowed): return value if isinstance(value,str) and value in allowed else '__unknown__'
    def block(b):
        if not isinstance(b,dict): return None
        typ=enum(b.get('type'),{'tool_use','tool_result','text','thinking','redacted_thinking','image','document','server_tool_use','web_search_tool_result','tool_reference'})
        out={'type':typ}
        if typ=='tool_use': out.update(id=ident(b.get('id')),name=name(b.get('name')),input={} if isinstance(b.get('input'),dict) else None)
        if typ=='tool_result':
            out.update(tool_use_id=ident(b.get('tool_use_id')),content='[content omitted]' if isinstance(b.get('content'),(str,list)) else None)
            if 'is_error' in b: out['is_error']=b['is_error'] if type(b['is_error']) is bool else None
        return out
    out=[]
    for _,r,error in records(text):
        if error: out.append('{INVALID_JSON'); continue
        typ=enum(r.get('type'),EXEC_TYPES|SESSION_TYPES|CLAUDE_TYPES)
        p={'type':typ}
        if typ.startswith('item.'):
            item=r.get('item')
            if isinstance(item,dict):
                it={'type':enum(item.get('type'),TOOLS|{'agent_message','reasoning','todo_list'})}
                if it['type'] in TOOLS:
                    it.update(id=ident(item.get('id')),status=enum(item.get('status'),{'completed','failed','declined','in_progress'}))
                    if type(item.get('exit_code')) is int: it['exit_code']=0 if item['exit_code']==0 else 1
                p['item']=it
        elif typ in SESSION_TYPES:
            src=r.get('payload')
            if isinstance(src,dict):
                target={}
                if typ in {'response_item','event_msg'}:
                    allowed={'function_call','custom_tool_call','function_call_output','custom_tool_call_output','message','reasoning','web_search_call','local_shell_call','compaction','image_generation_call','user_message','agent_message','agent_reasoning','token_count','task_started','task_complete','turn_aborted','context_compacted','thread_rolled_back','error','warning','item_started','item_completed','raw_response_item','exec_command_begin','exec_command_end','mcp_tool_call_begin','mcp_tool_call_end','patch_apply_begin','patch_apply_end','plan_update','shutdown_complete'}
                    target['type']=enum(src.get('type'),allowed)
                    if target['type'] in {'function_call','custom_tool_call'}: target.update(call_id=ident(src.get('call_id')),name=name(src.get('name')),arguments='{}')
                    elif target['type'] in {'function_call_output','custom_tool_call_output'}:
                        target['call_id']=ident(src.get('call_id'))
                        data=src.get('output')
                        target['output']={'exit_code':0 if data['exit_code']==0 else 1} if isinstance(data,dict) and type(data.get('exit_code')) is int else '[content omitted]'
                p['payload']=target
        elif typ in {'assistant','user'}:
            msg=r.get('message')
            if isinstance(msg,dict):
                content=msg.get('content')
                p['message']={'content':[block(b) for b in content] if isinstance(content,list) else '[content omitted]' if isinstance(content,str) else None}
                if 'role' in msg: p['message']['role']=msg['role'] if msg['role'] in ('assistant','user') else '__unknown__'
        elif typ=='result': p['is_error']=r.get('is_error') is True
        out.append(encode(p))
    return '\n'.join(out)+'\n'

def bundle(text,format='auto',focus=None):
    original=analyze(text,format)
    source_lines=[n for n,_,_ in records(text)]
    scope='full-structure'
    if focus is not None:
        if not isinstance(focus,str) or focus not in {f['code'] for f in original['findings']}: raise InputError('Choose an existing finding code for minimization.')
        selected={n for f in original['findings'] if f['code']==focus for n in f['lines'] if n is not None}
        if not selected: raise InputError('This finding has no record-local evidence to minimize.')
        for c in original['calls']:
            links={c['line'],c['resultLine']} - {None}
            if links & selected: selected.update(links)
        source_lines=sorted(selected)
        all_lines=text.splitlines()
        text='\n'.join(all_lines[n-1] for n in source_lines)+'\n'
        scope='finding-slice'
        if original['format'] in FORMATS[1:]: format=original['format']
        original=analyze(text,format)
    projected=project(text)
    sanitized=analyze(projected,format)
    same=signature(original)==signature(sanitized)
    # An exporter cannot promise semantic equivalence for unsupported source structures.
    # Preserve the failure to reproduce as an explicit result, never a fake successful replay.
    return dict(bundleVersion=1,kind='structural-parser-case',scope=scope,focus=focus,sourceLines=source_lines,parserVersion=VERSION,format=format,transcript=projected,expected=signature(sanitized),projectionVerified=same,originalSummary=signature(original),privacy=dict(policy='closed-allowlist-v1',omitted=['prose','commands','arguments','outputs','paths','URLs','timestamps','original IDs','custom tool names','unknown keys'],retained=['event structure','tool categories','failure booleans','zero/nonzero exit class','record order'],warning='Structural parser case only. Not an executable agent reproduction. Workflow structure may still be confidential. Review before sharing.'),sha256=digest(projected))

def verify_bundle(data):
    if not isinstance(data,dict) or data.get('bundleVersion')!=1 or data.get('kind')!='structural-parser-case': raise InputError('Not a supported structural parser bundle.')
    transcript=data.get('transcript')
    if not isinstance(transcript,str) or digest(transcript)!=data.get('sha256'): raise InputError('Bundle integrity check failed.')
    actual=analyze(transcript,data.get('format','auto'))
    verified=signature(actual)==data.get('expected')
    return dict(verified=verified,parserVersion=VERSION,bundleParserVersion=data.get('parserVersion'),actual=signature(actual),expected=data.get('expected'),note='Re-runs the local parser on sanitized structure. No agent or command was executed.')
