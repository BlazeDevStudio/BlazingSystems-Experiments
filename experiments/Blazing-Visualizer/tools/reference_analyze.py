"""Independent Spotify Python postprocessor and TFLite reference, not the Kotlin port."""
import argparse, json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from ai_edge_litert.interpreter import Interpreter
p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path,required=True);args=p.parse_args();sys.path.insert(0,str(args.upstream))
from basic_pitch.note_creation import model_output_to_notes
root=Path(__file__).resolve().parents[1];out=root/'fixtures'
runner=Interpreter(model_path=str(root/'app/src/main/assets/models/nmp.tflite'),num_threads=2);runner.allocate_tensors();signature=runner.get_signature_runner('serving_default')
for name in ('synthetic','flute'):
 rate,data=wavfile.read(out/f'{name}.wav');assert rate==22050;signal=data.astype(np.float32)/32768;full=np.concatenate([np.zeros(3840,dtype=np.float32),signal]);outputs={k:[] for k in ('note','onset','contour')};first=None
 for offset in range(0,len(full),36164):
  window=np.zeros(43844,dtype=np.float32);part=full[offset:offset+43844];window[:len(part)]=part;values=signature(input_2=window.reshape(1,43844,1))
  if first is None:first=values;window.tofile(out/f'{name}.window.f32')
  for k in outputs:outputs[k].append(values[k][0,15:157])
 count=int(len(signal)/36164*142);outputs={k:np.concatenate(v)[:count] for k,v in outputs.items()}
 _,events=model_output_to_notes(outputs,.5,.3,include_pitch_bends=False)
 result=[{'pitch':int(e[2]),'startUs':round(e[0]*1e6),'endUs':round(e[1]*1e6),'amplitude':float(e[3])} for e in sorted(events,key=lambda e:(e[0],e[2]))]
 (out/f'{name}.reference.json').write_text(json.dumps(result,indent=2)+'\n')
 if name=='synthetic':
  for key in ('note','onset','contour'):first[key].astype('<f4').tofile(out/f'first-window.{key}.f32');outputs[key].astype('<f4').tofile(out/f'full.{key}.f32')
 print(name,len(result),'notes',result,flush=True)
