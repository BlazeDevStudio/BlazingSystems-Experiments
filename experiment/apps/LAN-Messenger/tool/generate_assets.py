"""Generate original, dependency-free LAN Messenger sound and tray resources.
No third-party media files are bundled. Reproducible with Python stdlib.
"""
import math
import struct
import wave
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sound_dir=root/'assets/sounds'; sound_dir.mkdir(parents=True,exist_ok=True)
icon_dir=root/'assets/icons';icon_dir.mkdir(parents=True,exist_ok=True)
RATE=24000
MELODIES={
    'call': [(0.00,.21,523.25),(.24,.21,659.25),(.56,.21,523.25),(.80,.21,659.25)],
    'video_call':[(0.00,.13,783.99),(.15,.13,987.77),(.32,.26,1174.66),(.68,.17,987.77)],
    'message': [(0.00,.085,740.0),(.10,.11,987.77)],
    'file':[(0.00,.10,523.25),(.12,.10,659.25),(.24,.14,880.0)],
}
for key,notes in MELODIES.items():
    total=max(start+length for start,length,_ in notes)+.07
    samples=[]
    for i in range(int(total*RATE)):
        t=i/RATE
        value=0.0
        for start,length,hz in notes:
            elapsed=t-start
            if 0<=elapsed<=length:
                env=min(1,elapsed/.014, (length-elapsed)/.045)
                value+=.23*env*(math.sin(2*math.pi*hz*elapsed)+.24*math.sin(2*math.pi*2*hz*elapsed))
        samples.append(struct.pack('<h',max(-32768,min(32767,round(value*32767)))))
    with wave.open(str(sound_dir/(key+'.wav')),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE);wav.writeframes(b''.join(samples))
# Windows ICO: original pixel-drawn chat bubble, 32x32 BGRA plus AND mask.
W=H=32
pixel=[]
for y in range(H):
    for x in range(W):
        inside=(4<=x<=27 and 4<=y<=24 and (7<=x<=24 or 7<=y<=21)) or (8<=x<=14 and 24<=y<=28)
        if inside:
            bgra=(214,102,22,255)
            if 9<=y<=11 and 10<=x<=22 or 15<=y<=17 and 10<=x<=18:
                bgra=(255,255,255,255)
        else: bgra=(0,0,0,0)
        pixel.append(bytes(bgra))
rows=[]
for y in range(H-1,-1,-1): rows.append(b''.join(pixel[y*W:(y+1)*W]))
bitmap=b''.join(rows)
mask=b'\x00'*((W+31)//32*4*H)
header=struct.pack('<IiiHHIIiiII',40,W,2*H,1,32,0,len(bitmap)+len(mask),0,0,0,0)
frame=header+bitmap+mask
ico=struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',W,H,0,0,1,32,len(frame),22)+frame
(icon_dir/'lan_messenger.ico').write_bytes(ico)
print('Created',len(MELODIES),'alert sounds and tray icon')