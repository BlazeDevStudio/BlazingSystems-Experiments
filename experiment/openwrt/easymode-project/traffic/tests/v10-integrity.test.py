#!/usr/bin/env python3
"""Synthetic positive and negative tests for the V10 read-only integrity verifier."""
import hashlib
import io
import json
import pathlib
import shutil
import subprocess
import tarfile
import tempfile

TOOL = pathlib.Path(__file__).resolve().parents[1] / 'tools/verify-r281-v10.py'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def invoke(file):
    return subprocess.run(['python3', str(file)], text=True, capture_output=True)

def main():
    with tempfile.TemporaryDirectory() as temp:
        project=pathlib.Path(temp)/'easymode-project'
        release=project/'releases/v10.0.0-r281'
        (project/'traffic/tools').mkdir(parents=True)
        verifier=project/'traffic/tools/verify-r281-v10.py'
        shutil.copy2(TOOL,verifier)
        (release/'root/etc/blaze').mkdir(parents=True)
        version=release/'root/etc/blaze/easymode-version'
        version.write_bytes(b'10.0.0\n')
        (release/'install.sh').write_bytes(b'#!/bin/sh\n')
        payload={'root/etc/blaze/easymode-version':(b'10.0.0\n',0o644),
                 'install.sh':(b'#!/bin/sh\n',0o755)}
        manifest={'version':'10.0.0','board':'notion,r281','openwrt':'24.10.8',
                  'files':[{'path':name,'mode':f'{mode:04o}','bytes':len(data),'sha256':digest(data)}
                           for name,(data,mode) in payload.items()]}
        mb=(json.dumps(manifest,indent=2)+'\n').encode()
        (release/'SOURCE-MANIFEST.json').write_bytes(mb)
        payload.update({'SOURCE-MANIFEST.json':(mb,0o644),'VERSION':(b'10.0.0\n',0o644)})
        sums=''.join(f'{digest(data)}  {name}\n' for name,(data,mode) in sorted(payload.items()))
        payload['SHA256SUMS']=(sums.encode(),0o644)
        (release/'openwrt').mkdir()
        archive=release/'openwrt/EasyMode-v10.0.0-R281-app-update.tar.gz'
        def write_archive(modified=None):
            with tarfile.open(archive,'w:gz') as stream:
                for name,(data,mode) in payload.items():
                    if name==modified:
                        data+=b'CORRUPTION'
                    item=tarfile.TarInfo(name)
                    item.mode=mode
                    item.size=len(data)
                    stream.addfile(item,io.BytesIO(data))
            side=archive.with_suffix(archive.suffix+'.sha256')
            side.write_text(f'{digest(archive.read_bytes())}  {archive.name}\n')

        write_archive()
        result=invoke(verifier)
        assert result.returncode==0,(result.stdout,result.stderr)
        print('PASS: clean V10 fixture')

        write_archive('install.sh')
        result=invoke(verifier)
        assert result.returncode!=0 and 'Archive/source mismatch' in result.stderr,result.stderr
        print('PASS: tampered archive rejected')

        write_archive()
        version.write_bytes(b'10.0.1\n')
        result=invoke(verifier)
        assert result.returncode!=0 and 'Source tree differs from manifest' in result.stderr,result.stderr
        print('PASS: source/manifest drift rejected')

if __name__=='__main__':
    main()
