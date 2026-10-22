"""Reproducible synthetic notes and CC0 sampled-flute acceptance clips."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
import json, hashlib, io, wave
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
from math import gcd
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'fixtures';OUT.mkdir(exist_ok=True)
SR=22050

def save(name,signal,events,license):
 pcm=(np.clip(signal,-1,1)*32767).astype('<i2');path=OUT/(name+'.wav');wavfile.write(path,SR,pcm)
 (OUT/(name+'.expected.json')).write_text(json.dumps({'sampleRate':SR,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'events':events,'license':license},indent=2)+'\n')

def synth():
 signal=np.zeros(4*SR);events=[]
 for start,end,pitches in [(.3,1.3,[60]),(1.5,2.5,[64]),(2.7,3.7,[60,64,67])]:
  t=np.arange(round((end-start)*SR))/SR;env=np.minimum(1,t/.015)*np.minimum(1,(end-start-t)/.08)*np.exp(-.65*t)
  for pitch in pitches:
   hz=440*2**((pitch-69)/12);tone=sum(np.sin(2*np.pi*hz*h*t)/h**1.7 for h in range(1,7))*.2*env
   offset=round(start*SR);signal[offset:offset+len(tone)]+=tone;events.append({'pitch':pitch,'startUs':round(start*1e6),'endUs':round(end*1e6)})
 save('synthetic',signal,events,'Original generated fixture; CC0')

def flute():
 commit='440300901dfe9275fd84e0b7763af1f8443ae62e';base=f'https://raw.githubusercontent.com/sgossner/VSCO-2-CE/{commit}/'
 signal=np.zeros(round(4.5*SR));events=[]
 for label,pitch,start in [('C4',72,.3),('E4',76,1.6),('A4',81,2.9)]:
  data=urlopen(base+quote(f'Woodwinds/Flute/stac/LDFlute_stac_{label}_v2_rr1.wav')).read();rate,sample=wavfile.read(io.BytesIO(data));sample=sample.astype(np.float64)/(32768 if sample.dtype==np.int16 else 2147483648)
  if sample.ndim>1:sample=sample.mean(axis=1)
  d=gcd(rate,SR);sample=resample_poly(sample,SR//d,rate//d);sample=sample[np.flatnonzero(np.abs(sample)>np.max(np.abs(sample))*.01)[0]:];sample=sample[:round(.9*SR)];sample=sample/np.max(np.abs(sample))*.5
  offset=round(start*SR);signal[offset:offset+len(sample)]+=sample;events.append({'pitch':pitch,'startUs':round(start*1e6),'endUs':round((start+len(sample)/SR)*1e6)})
 license=urlopen(base+'LICENSE').read().decode();(OUT/'VSCO-LICENSE.txt').write_text(license)
 save('flute',signal,events,'VSCO 2 CE / Sam Gossner and Simon Dalzell; CC0; samples cut by Elan Hickler; pinned '+commit)
if __name__=='__main__':synth();flute()
