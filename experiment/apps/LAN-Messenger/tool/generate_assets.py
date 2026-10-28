"""Generate original, dependency-free LAN Messenger sound and tray resources.
No third-party media files are bundled. Reproducible with Python stdlib.
"""
import math
import wave
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sound_dir=root/'assets/sounds'; sound_dir.mkdir(parents=True,exist_ok=True)
icon_dir=root/'assets/icons';icon_dir.mkdir(parents=True,exist_ok=True)
RATE=24000
MELODIES={
    # Original four-note corporate-style audible cues with soft attack/release.
    'call': [(0,.28,392.0),(.36,.28,523.25),(.76,.28,587.33),(1.16,.36,523.25)],
    'video_call':[(0,.20,440.0),(.26,.20,554.37),(.56,.21,659.25),(.83,.40,783.99)],
    'message': [(0,.12,783.99),(.14,.24,1046.50)],
    'file':[(0,.15,523.25),(.18,.15,659.25),(.38,.33,783.99)],
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
                env=min(1,elapsed/.045, (length-elapsed)/.10)
                value+=.26*env*(.88*math.sin(2*math.pi*hz*elapsed)
                    + .09*math.sin(2*math.pi*2*hz*elapsed)
                    + .03*math.sin(2*math.pi*3*hz*elapsed))
        samples.append(struct.pack('<h',max(-32768,min(32767,round(value*32767)))))
    with wave.open(str(sound_dir/(key+'.wav')),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE);wav.writeframes(b''.join(samples))
# Use exact owner-provided ConnectIT icon; do not recreate the old bubble.
import shutil
icon_source = root/'assets/branding/connectit/connectit.ico'
if not icon_source.is_file():
    raise FileNotFoundError(f'Missing ConnectIT icon: {icon_source}')
shutil.copyfile(icon_source, icon_dir/'lan_messenger.ico')
print('Created',len(MELODIES),'sounds and installed ConnectIT icon')
