import argparse
import json
import sys
from pathlib import Path
from .core import analyze, bundle, compare, verify_bundle, InputError, FORMATS, MAX_BYTES, VERSION, strict_loads

def read(path):
    p=Path(path)
    if p.stat().st_size>MAX_BYTES: raise InputError('Input exceeds 16 MiB.')
    return p.read_text(encoding='utf-8')

def main(argv=None):
    parser=argparse.ArgumentParser(prog='incidentlab',description='Offline native agent transcript inspection. Never executes agent commands.')
    parser.add_argument('--version',action='version',version=VERSION)
    subs=parser.add_subparsers(dest='command',required=True)
    for command in ('inspect','bundle'):
        p=subs.add_parser(command)
        p.add_argument('file');p.add_argument('--format',choices=FORMATS,default='auto');p.add_argument('--out')
        if command=='bundle': p.add_argument('--focus',help='Keep source evidence for one finding code and linked call/result records.')
        if command=='inspect': p.add_argument('--gate',action='store_true',help='Exit 2 for incomplete parsing, explicit failure, or invalid correlation.')
    p=subs.add_parser('compare');p.add_argument('before');p.add_argument('after');p.add_argument('--format',choices=FORMATS,default='auto');p.add_argument('--out')
    p=subs.add_parser('verify');p.add_argument('file');p.add_argument('--out')
    p=subs.add_parser('serve');p.add_argument('--port',type=int,default=8765)
    args=parser.parse_args(argv)
    try:
        if args.command=='serve':
            from .server import serve
            serve(args.port);return 0
        if args.command=='inspect': result=analyze(read(args.file),args.format)
        elif args.command=='bundle': result=bundle(read(args.file),args.format,args.focus)
        elif args.command=='compare': result=compare(analyze(read(args.before),args.format),analyze(read(args.after),args.format))
        else: result=verify_bundle(strict_loads(read(args.file)))
        output=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
        if args.out: Path(args.out).write_text(output,encoding='utf-8')
        else:
            print(output,end='')
            sys.stdout.flush()
        if args.command=='inspect' and args.gate and not result['quality']['gate']: return 2
        if args.command=='verify' and not result['bundleChecksPassed']: return 2
        return 0
    except BrokenPipeError:
        # A downstream consumer (for example head) closed stdout intentionally.
        try:
            sys.stdout.close()
        except OSError:
            pass
        return 0
    except (OSError,UnicodeError,ValueError,RecursionError) as exc:
        print(f'incidentlab: {exc}',file=sys.stderr);return 1
