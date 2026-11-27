package com.blazesystems.blazerental;

import android.content.Context;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

public final class LeaseClient {
    private LeaseClient(){}
    public static boolean sync(Context c){
        try{
            String base=LeaseStore.server(c);if(base.isEmpty())return false;
            String secret=LeaseStore.deviceSecret(c),enroll=LeaseStore.enrollment(c),nonce=Hmac.nonce();
            String action=secret.isEmpty()?"enroll":"status",authSecret=secret.isEmpty()?enroll:secret;if(authSecret.isEmpty())return false;
            String extra;
            if(secret.isEmpty()){int dot=enroll.indexOf('.');if(dot<=0)return false;extra="&enroll_id="+enc(enroll.substring(0,dot));}
            else extra="&device_id="+enc(LeaseStore.deviceId(c))+"&inventory="+enc(Policy.inventoryCsv(c));
            String body="action="+action+"&nonce="+enc(nonce)+extra+"&sig="+enc(Hmac.sha256Hex(authSecret,action+"|"+nonce+"|"+authSecret));
            JSONObject j=post(base,body);if(j==null||!j.optBoolean("ok",false))return false;
            String newSecret=j.optString("device_secret",secret),deviceId=j.optString("device_id",LeaseStore.deviceId(c));
            if(!deviceId.isEmpty()&&!newSecret.isEmpty())LeaseStore.setDeviceIdentity(c,deviceId,newSecret);
            long now=j.optLong("server_time_ms",0),until=j.optLong("lease_until_ms",0);if(now<=0||until<now)return false;
            if(action.equals("status")){
                String allowed=j.optString("allowed_packages","*"),salt=j.optString("admin_salt",""),hash=j.optString("admin_hash",""),preferred=j.optString("preferred_vendo","");
                int rounds=j.optInt("admin_rounds",4096),per=j.optInt("rental_seconds_per_pulse",600);String sig=j.optString("policy_sig","");
                String canonical=deviceId+"|"+nonce+"|"+now+"|"+until+"|"+allowed+"|"+salt+"|"+hash+"|"+rounds+"|"+preferred+"|"+per;
                if(sig.isEmpty()||!sig.equals(Hmac.sha256Hex(newSecret,canonical)))return false;
                LeaseStore.recordServerState(c,now,until,newSecret,allowed,salt,hash,rounds,preferred,per);
            }else LeaseStore.recordServerState(c,now,until,newSecret,"*","","",4096,"",600);
            Policy.applyManagedPolicy(c);return true;
        }catch(Exception ignored){return false;}
    }
    public static String coinStart(Context c){
        try{
            String base=LeaseStore.server(c),secret=LeaseStore.deviceSecret(c),did=LeaseStore.deviceId(c);if(base.isEmpty()||secret.isEmpty()||did.isEmpty())return "Rental phone is not enrolled.";
            String nonce=Hmac.nonce(),preferred=LeaseStore.preferredVendo(c);
            String body="action=coin_start&nonce="+enc(nonce)+"&device_id="+enc(did)+"&sig="+enc(Hmac.sha256Hex(secret,"coin_start|"+nonce+"|"+secret));
            if(!preferred.isEmpty())body+="&vendo="+enc(preferred);
            JSONObject j=post(base,body);if(j==null)return "Server unavailable.";if(!j.optBoolean("ok",false))return j.optString("error","Unable to start coin slot.");
            return "Insert coin at "+j.optString("vendo","selected controller")+".";
        }catch(Exception e){return "Unable to start coin slot.";}
    }
    private static JSONObject post(String base,String body)throws Exception{
        URL u=new URL(base.replaceAll("/+$","")+"/cgi-bin/rental");HttpURLConnection h=(HttpURLConnection)u.openConnection();
        h.setConnectTimeout(3500);h.setReadTimeout(3500);h.setRequestMethod("POST");h.setDoOutput(true);h.setRequestProperty("Content-Type","application/x-www-form-urlencoded");
        try(OutputStream o=h.getOutputStream()){o.write(body.getBytes(StandardCharsets.UTF_8));}
        InputStream in=(h.getResponseCode()==200)?h.getInputStream():h.getErrorStream();if(in==null)return null;return new JSONObject(read(in));
    }
    private static String enc(String s)throws Exception{return URLEncoder.encode(s,"UTF-8");}
    private static String read(InputStream in)throws Exception{ByteArrayOutputStream b=new ByteArrayOutputStream();byte[] x=new byte[2048];int n;while((n=in.read(x))>0)b.write(x,0,n);return b.toString("UTF-8");}
}
