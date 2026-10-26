#!/usr/bin/env python3
"""Deterministic interpreted OpenWrt packages. No target binaries are fabricated."""
import argparse, gzip, hashlib, io, json, pathlib, re, tarfile
BASE=pathlib.Path(__file__).resolve().parents[2]
VERSION='7.0.2'
EDITIONS=['generic','ap','router','cellular','switch','pc']
DEPS='ucode, ucode-mod-fs, ucode-mod-uci, ucode-mod-ubus, rpcd, rpcd-mod-ucode, uhttpd-mod-ubus, nftables-json'
def tar(files):
 out=io.BytesIO()
 with gzip.GzipFile(fileobj=out,mode='wb',mtime=0,filename='') as gz:
  with tarfile.open(fileobj=gz,mode='w',format=tarfile.GNU_FORMAT) as t:
   # opkg does not create missing parents for regular members itself.
   directories=set()
   for name in files:
    directories.update(str(p) for p in pathlib.PurePosixPath(name).parents if str(p)!='.')
   for name in sorted(directories,key=lambda n:(n.count('/'),n)):
    item=tarfile.TarInfo('./'+name+'/');item.type=tarfile.DIRTYPE;item.mode=0o755;item.uid=item.gid=0;item.mtime=0;t.addfile(item)
   for name,(data,mode) in sorted(files.items()):
    item=tarfile.TarInfo('./'+name);item.size=len(data);item.mode=mode;item.uid=item.gid=0;item.mtime=0;t.addfile(item,io.BytesIO(data))
 return out.getvalue()
def executable(path):return '/init.d/' in path or '/libexec/' in path or '/uci-defaults/' in path or path.endswith('.sh')
def payload():
 return {p.relative_to(BASE/'traffic/root').as_posix():(p.read_bytes(),0o755 if executable('/'+p.relative_to(BASE/'traffic/root').as_posix()) else 0o644) for p in (BASE/'traffic/root').rglob('*') if p.is_file()}
def package(name,files,depends,extra='',scripts=None):
 control=f'Package: {name}\nVersion: {VERSION}-1\nArchitecture: all\nMaintainer: BlazingSystems\nSection: admin\nPriority: optional\nLicense: GPL-2.0-only\nDepends: {depends}\nDescription: EasyMode Traffic Intelligence\n{extra}'
 ctl={'control':(control.encode(),0o644)};ctl.update(scripts or {})
 return tar({'debian-binary':(b'2.0\n',0o644),'control.tar.gz':(tar(ctl),0o644),'data.tar.gz':(tar(files),0o644)})
def check():
 files=payload();assert files and sum(len(v[0]) for v in files.values())<512000
 for name,(data,_) in files.items():
  assert not name.startswith('/') and '..' not in pathlib.PurePosixPath(name).parts
  assert b'\r\n' not in data,name+' must use LF'
  assert not re.search(rb'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----)',data),name
  if name.endswith('.json'):json.loads(data)
 assert set(EDITIONS)=={p.name for p in (BASE/'editions').iterdir() if p.is_dir()}
 print(f'PASS: {len(files)} payload files, {sum(len(v[0]) for v in files.values())} bytes; paths, JSON, line endings and credential scan')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--output',default=str(BASE/'dist-v7'));args=parser.parse_args();check()
 if args.check:return
 out=pathlib.Path(args.output);out.mkdir(exist_ok=True,parents=True);files=payload()
 post=(BASE/'traffic/tools/postinst').read_bytes();pre=(BASE/'traffic/tools/prerm').read_bytes()
 core_name=f'EasyMode-v{VERSION}-Core-all.ipk';core=package('easymode-traffic',files,DEPS,scripts={'postinst':(post,0o755),'prerm':(pre,0o755),'conffiles':(b'/etc/config/easymode_traffic\n',0o644)})
 (out/core_name).write_bytes(core)
 for edition in EDITIONS:
  script=f'''#!/bin/sh
[ -n "$IPKG_INSTROOT" ] && exit 0
uci set easymode_traffic.main.edition='{edition}'
uci commit easymode_traffic
/etc/init.d/easymode-traffic reload
exit 0
'''.encode()
  marker={'usr/share/easymode-traffic/edition-'+edition:(edition.encode(),0o644)}
  other=', '.join('easymode-'+e for e in EDITIONS if e!=edition)
  data=package('easymode-'+edition,marker,f'easymode-traffic (= {VERSION}-1)',f'Provides: easymode-edition\nConflicts: {other}\n',{'postinst':(script,0o755)})
  name=f'EasyMode-v{VERSION}-{edition.title()}-all.ipk';(out/name).write_bytes(data)
  sums=f'{hashlib.sha256(core).hexdigest()}  {core_name}\n{hashlib.sha256(data).hexdigest()}  {name}\n'.encode()
  bundle={core_name:(core,0o644),name:(data,0o644),'PACKAGE-SHA256SUMS':(sums,0o644),'install.sh':((BASE/'traffic/tools/install.sh').read_bytes(),0o755),'README.md':((BASE/'traffic/README.md').read_bytes(),0o644),'Update-EasyMode.ps1':((BASE/'traffic/tools/Update-EasyMode.ps1').read_bytes(),0o644),'Update-EasyMode.bat':(b'@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Update-EasyMode.ps1"\r\npause\r\n',0o644)}
  (out/f'EasyMode-v{VERSION}-{edition.title()}-offline.tar.gz').write_bytes(tar(bundle))
 manifest={'version':VERSION,'package_architecture':'all','format':'OpenWrt opkg IPK','runtime':'OpenWrt 24.10, ucode/rpcd','editions':EDITIONS,'hardware_tests':'R281 OpenWrt 24.10.8 preview installation and live API/browser checks passed; other hardware NOT HARDWARE VERIFIED; see TEST-REPORT.md','files':[]}
 for p in sorted(out.glob('*')):
  if p.is_file() and p.name not in ['SHA256SUMS','BUILD-MANIFEST.json']:manifest['files'].append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 (out/'BUILD-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS');(out/'SHA256SUMS').write_text(sums,encoding='ascii')
 print(f'Built {len(manifest["files"])} installable package/archive artifacts in {out}')
if __name__=='__main__':main()
