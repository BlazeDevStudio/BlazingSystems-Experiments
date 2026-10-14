#!/usr/bin/env python3
"""Build the narrowly scoped, no-config R281 management update archive."""
import hashlib, io, json, pathlib, tarfile
from build import tar
BASE=pathlib.Path(__file__).resolve().parents[2]
ROOT=BASE/'releases/v4.2.6-r281-consolidated/root'
PATHS=['usr/share/blaze/sms-archive-core.uc','usr/share/blaze/sms-inbox-archive.uc','usr/share/blaze/message.uc','usr/share/rpcd/ucode/blaze','usr/libexec/blaze-sms-archive-daemon','etc/init.d/blaze-sms-archive','www/easy/app.js','www/easy/core.js','www/easy/style.css','www/index.html']
FILES={'root/'+p:(ROOT.joinpath(p).read_text(encoding='utf-8').encode(),0o755 if ('/libexec/' in p or '/init.d/' in p) or p.endswith('.sh') else 0o644) for p in PATHS}
FILES['install.sh']=((BASE/'traffic/tools/r281-update-install.sh').read_bytes(),0o755)
FILES['README.md']=((BASE/'traffic/R281-WIFI-UPDATE.md').read_bytes(),0o644)
FILES['SHA256SUMS']=(''.join(hashlib.sha256(d).hexdigest()+'  '+p+'\n' for p,(d,_) in sorted(FILES.items())).encode(),0o644)
out=BASE/'releases/v4.2.6-r281-consolidated/openwrt';out.mkdir(exist_ok=True)
archive=out/'EasyMode-R281-4.2.6-SMS-ARCHIVE-20261015.tar.gz'
archive.write_bytes(tar(FILES))
with tarfile.open(archive) as t:
 for p,(data,mode) in FILES.items():
  assert t.extractfile('./'+p).read()==data,p
  assert t.getmember('./'+p).mode==mode,p
archive.with_suffix(archive.suffix+'.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print('PASS: archive payload, permissions and checksums verified:',archive)
