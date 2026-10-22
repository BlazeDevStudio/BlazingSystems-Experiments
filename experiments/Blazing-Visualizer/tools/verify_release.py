"""Audit the preview APK and fresh, device-produced acceptance evidence."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,zipfile,xml.etree.ElementTree as E
p=argparse.ArgumentParser();p.add_argument('--apk',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--instrumentation-log',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
root=Path(__file__).resolve().parents[1];report={'apk':args.apk.name,'apkSha256':hashlib.sha256(args.apk.read_bytes()).hexdigest(),'sourceRevision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()}
report['sourceDirty']=bool(subprocess.check_output(['git','status','--porcelain','--','app/src/main','app/build.gradle.kts','build.gradle.kts','settings.gradle.kts','gradle.properties','gradle'],cwd=root).strip())
checks={}
with zipfile.ZipFile(args.apk) as z:
 model=z.read('assets/models/nmp.tflite');checks['modelSha256']=hashlib.sha256(model).hexdigest();assert checks['modelSha256']=='3db297d54af8e01c6e5618245c956b1d71b6a2b978cb2dedb527173186552676'
 libs={}
 for n in z.namelist():
  if n.startswith('lib/') and n.endswith('.so'):
   b=z.read(n);assert b[:5]==b'\x7fELF\x02';phoff=struct.unpack_from('<Q',b,32)[0];entsize,count=struct.unpack_from('<HH',b,54);alignments=[struct.unpack_from('<IIQQQQQQ',b,phoff+i*entsize)[-1] for i in range(count) if struct.unpack_from('<I',b,phoff+i*entsize)[0]==1];assert alignments and min(alignments)>=16384,(n,alignments);libs[n]=alignments
 checks['nativeLoadAlignment']=libs;assert any('/arm64-v8a/' in n for n in libs) and any('/x86_64/' in n for n in libs)
xmls=list((root/'app/build/test-results/testDebugUnitTest').glob('TEST-*.xml'));assert xmls
checks['hostTests']=0
for f in xmls:
 x=E.parse(f).getroot();assert int(x.attrib['failures'])==0 and int(x.attrib['errors'])==0;checks['hostTests']+=int(x.attrib['tests'])
log=args.instrumentation_log.read_text();assert 'OK (11 tests)' in log and 'FAILURES!!!' not in log
checks['deviceTests']=11
for name in ('synthetic-accuracy','flute-accuracy'):
 data=json.loads((args.evidence/(name+'.json')).read_text());assert data['rawF1']>=.8 and data['onsetToleranceUs']==50000;checks[name]=data
matrix=json.loads((args.evidence/'export-matrix.json').read_text())['results'];expected={(1280,720),(720,1280),(720,720),(1920,1080),(1080,1920),(1080,1080),(320,180)};assert {(v['width'],v['height']) for v in matrix}==expected
for v in matrix:
 tracks=v['tracks'];assert len(tracks)==2;duration=4_000_000 if v['width']==320 else 100_000
 assert {t['mime'] for t in tracks}=={'video/avc','audio/mp4a-latm'}
 for t in tracks:assert abs(t['durationUs']-duration)<=50000 and 0<=t['firstPtsUs']<=50000 and t['samples']>0
checks['exportMatrix']=matrix
alignment=json.loads((args.evidence/'audio-alignment.json').read_text());assert abs(alignment['bestLagUs'])<=50000 and alignment['normalizedCorrelation']>.8;checks['audioAlignment']=alignment
parity=json.loads((args.evidence/'model-parity.json').read_text());assert max(parity.values())<.001;checks['modelParityMaxErrors']=parity
checks['rendererParity']=json.loads((args.evidence/'renderer-parity.json').read_text())
report.update({'checks':checks,'releaseStatus':'preview','physicalDeviceVerified':False});args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'apkSha256':report['apkSha256'],'hostTests':checks['hostTests'],'deviceTests':checks['deviceTests'],'status':'PASS'}))
