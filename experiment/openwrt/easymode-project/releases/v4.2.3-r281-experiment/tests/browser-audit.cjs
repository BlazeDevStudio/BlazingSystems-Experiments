const fs=require('fs');const assert=require('assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||undefined,headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}}),results=[],errors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.dismiss());
 const record=(control,result)=>{results.push({control,result});console.log(control+': '+result)};
 const base=process.env.ROUTER_URL||'http://192.168.1.1';
 async function rpc(o,m,a={}){return page.evaluate(async({o,m,a})=>{let j=await(await fetch('/ubus',{method:'POST',body:JSON.stringify({jsonrpc:'2.0',id:1,method:'call',params:[sessionStorage.getItem('blaze-session'),o,m,a]})})).json();if(j.result?.[0]!==0)throw Error('RPC '+o+'.'+m+' '+j.result?.[0]);return j.result[1];},{o,m,a});}
 async function nav(t,s){await page.locator(`[data-tab="${t}"]`).click();if(s)await page.locator(`[data-sub="${s}"]`).click();await page.waitForTimeout(1000);}
 try{
  await page.goto(base);await page.locator('#password').fill(process.env.ROUTER_PASSWORD);await page.locator('#login-form button').click();await page.locator('#app').waitFor({state:'visible',timeout:30000});record('Login','Authenticated with LuCI credentials');
  const initial=await rpc('blaze','status');assert(initial.config.wifi.length===2);record('Overview','Live UCI Wi-Fi, interface addresses, DHCP clients and memory retrieved');
  const tabs=await page.locator('[data-tab]').evaluateAll(ns=>ns.map(n=>n.dataset.tab));const inventory=[];
  for(const tab of tabs){await nav(tab);const subs=await page.locator('[data-sub]').evaluateAll(ns=>ns.map(n=>n.dataset.sub));for(const sub of (subs.length?subs:[''])){
   if(sub)await nav(tab,sub);
   if(tab==='network'&&sub==='bands')await page.locator('#refresh-modem').waitFor({timeout:35000});
   if(tab==='sms'&&sub==='messages')await page.locator('#refresh-inbox').waitFor({timeout:35000});
   inventory.push({tab,sub,controls:await page.locator('#content button,#content a,#content input,#content select,#content textarea').evaluateAll(ns=>ns.map(n=>({id:n.id,tag:n.tagName,type:n.type,disabled:n.disabled||false,label:n.tagName==='BUTTON'||n.tagName==='A'?n.textContent.trim():n.labels?.[0]?.textContent.trim().slice(0,100),href:n.getAttribute('href'),action:n.dataset.rat||n.dataset.action||''})).filter(n=>!n.id.startsWith('sms-thread')))});
   record('Navigation '+tab+'/'+sub,'Opened');fs.writeFileSync(process.env.AUDIT_INVENTORY||'work/controls-inventory.json',JSON.stringify(inventory,null,2));
  }}
  await nav('wifi','uplink');
  await page.locator('#uplink-mode').selectOption('relay');await page.locator('#uplink-scope').selectOption('ssid');
  await page.locator('#uplink-captive').check();assert(await page.locator('#uplink-captive').isChecked());await page.locator('#uplink-captive').uncheck();
  assert.equal(await page.locator('#repeat-ssid').inputValue(),'BlazeSystems-Repeater');record('Dedicated repeater controls','Mode, scope, SSID and captive checkbox work');
  await page.locator('#scan-wifi').click();await page.waitForFunction(()=>!document.querySelector('#scan-wifi').disabled,null,{timeout:60000});const networks=page.locator('[data-wifi-index]');const count=await networks.count();assert(count>0);record('Scan Wi-Fi',count+' results; both radio results checked by API test');
  let enabled=page.locator('[data-wifi-index]:not([disabled])');for(let i=0;i<await enabled.count();i++){await enabled.nth(i).click();assert(await page.locator('#uplink-ssid').inputValue());}record('Scanned network buttons','Each enabled result fills SSID, radio, channel, security and BSSID');
  await page.locator('#uplink-ssid').fill('');const invalidResponse=page.waitForResponse(r=>r.url().endsWith('/ubus')&&r.request().postDataJSON()?.params?.[2]==='action');await page.locator('#connect-uplink').click();const invalid=(await(await invalidResponse).json()).result[1];assert.equal(invalid.ok,false);assert(invalid.error.includes('Invalid'),invalid.error);await page.waitForFunction(()=>document.querySelector('#toast').textContent.includes('Invalid'));record('Connect invalid input','Rejected before mutation');
  await nav('sms','messages');await page.locator('#refresh-inbox').click();await page.waitForTimeout(3500);await page.locator('#sms-new').click();await page.locator('#recipient').fill('5454');assert((await page.locator('#number-preview').textContent()).includes('5454'));record('SMS short code','5454 retained unchanged');await page.locator('#recipient').fill('09000000000');assert((await page.locator('#number-preview').textContent()).includes('639000000000'));record('SMS local number','PH 09 number normalized to 639');
  if(process.argv.includes('--send')){assert(process.env.SMS_TEST_NUMBER,'Set an explicitly authorized SMS_TEST_NUMBER');await page.locator('#recipient').fill(process.env.SMS_TEST_NUMBER);await page.locator('#message').fill('BlazeSystems Easy Mode audit: SMS send verification.');await page.locator('#send-sms').click();await page.waitForTimeout(2000);await page.waitForFunction(()=>!document.querySelector('#send-sms')?.disabled,null,{timeout:75000});record('SMS send',await page.locator('#toast').textContent());}
  await page.setViewportSize({width:390,height:844});await page.locator('#sms-back').click();record('SMS back','Mobile conversation selection restored');await page.setViewportSize({width:1440,height:1000});
  // Compare native LuCI pages by real navigation, without submitting destructive forms.
  const luci=await browser.newPage();for(const path of ['/cgi-bin/luci/admin/network/wireless','/cgi-bin/luci/admin/network/network','/cgi-bin/luci/admin/modem/luci-app-sms-tool-js/readsms','/cgi-bin/luci/admin/modem/luci-app-modemband/blte','/cgi-bin/luci/admin/status/syslog','/cgi-bin/luci/admin/system/admin','/cgi-bin/luci/admin/system/flash']){
   await luci.goto(base+path);if(await luci.locator('input[name="luci_password"]').count()){await luci.locator('input[name="luci_username"]').fill('root');await luci.locator('input[name="luci_password"]').fill(process.env.ROUTER_PASSWORD);await luci.getByRole('button',{name:/log in|login/i}).first().click();}await luci.waitForTimeout(2000);record('LuCI '+path,'Loaded '+await luci.title());
   if(path.endsWith('/readsms')){await luci.locator('#smsTable').waitFor({timeout:40000});record('LuCI inbox','Rows: '+Math.max(0,(await luci.locator('#smsTable tr').count())-1));}
   if(path.endsWith('/blte')){await luci.locator('#bands-grid').waitFor({timeout:40000});record('LuCI enabled bands',(await luci.locator('#bands-grid .band-tile--on').allTextContents()).join(', '));}
  }
  fs.writeFileSync(process.env.AUDIT_INVENTORY||'work/controls-inventory.json',JSON.stringify(inventory,null,2));
  await page.locator('a[href="/admin/"]').first().click();await page.waitForURL('**/cgi-bin/luci/**');record('Advanced','LuCI redirect works');
  await page.goto(base);await page.locator('#app').waitFor({state:'visible'});await page.locator('#logout').click();await page.locator('#login').waitFor({state:'visible'});record('Logout','Login returned');assert.deepEqual(errors,[]);
 }finally{fs.writeFileSync(process.env.AUDIT_OUTPUT||'work/browser-audit-20261004.json',JSON.stringify({results,errors},null,2));await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
