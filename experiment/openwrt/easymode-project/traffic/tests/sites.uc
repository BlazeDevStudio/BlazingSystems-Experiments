import {profile,effective,denied,question,response,answerNames} from '/usr/share/blaze/sites.uc';
let n=0;function check(v,m){if(!v)die(m);n++;}function rejects(f){let ok=false;try{f();}catch(e){ok=true;}check(ok,'must reject');}
let p=profile({enabled:true,mode:'deny',domains:['Example.COM'],devices:[{mac:'02:11:22:33:44:55',mode:'allow',domains:['openwrt.org']}]});
check(denied(p,'www.example.com'),'subdomain');check(!denied(p,'notexample.com'),'suffix boundary');check(!denied(p,'example.com.evil.test'),'suffix spoof');
let d=effective(p,'02:11:22:33:44:55');check(!denied(d,'downloads.openwrt.org'),'device allow');check(denied(d,'example.com'),'device deny');check(effective(p,'02:11:22:33:44:56').mode=='deny','default');
rejects(()=>profile({...p,domains:['https://example.com/path']}));rejects(()=>profile({...p,devices:[{mac:'ff:ff:ff:ff:ff:ff',mode:'off',domains:[]}]}));
let q='\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01';
check(question(q).name=='example.com','DNS name');let r=response(q,5);check(ord(r,3)==133&&substr(r,0,2)=='\x12\x34','REFUSED reply');
rejects(()=>question(substr(q,0,15)));rejects(()=>question(substr(q,0,12)+'\xc0\x0c\x00\x01\x00\x01'));
check(length(answerNames(r))==0,'empty refused records');check(effective({...p,enabled:false},'').mode=='off','master off');
print('PASS: '+n+' site policy and DNS parser checks\n');
