package com.blazesystems.blazerental;

import android.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class Hmac {
    private Hmac(){}
    public static String sha256Hex(String secret,String message) throws Exception {
        Mac m=Mac.getInstance("HmacSHA256");
        m.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8),"HmacSHA256"));
        return hex(m.doFinal(message.getBytes(StandardCharsets.UTF_8)));
    }
    public static String digestHex(String message) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(message.getBytes(StandardCharsets.UTF_8)));
    }
    public static String sha256Iter(String password,String salt,int rounds) throws Exception {
        if(rounds<1) rounds=1;
        String v=digestHex(salt+"|"+password+"|"+salt);
        for(int i=1;i<rounds;i++) v=digestHex(v+"|"+password+"|"+salt);
        return v;
    }
    private static String hex(byte[] b){
        StringBuilder s=new StringBuilder(b.length*2);
        for(byte x:b) s.append(String.format("%02x",x&0xff));
        return s.toString();
    }
    public static String nonce(){
        byte[] b=new byte[12]; new java.security.SecureRandom().nextBytes(b);
        String s=Base64.encodeToString(b,Base64.URL_SAFE|Base64.NO_WRAP|Base64.NO_PADDING);
        return s.replace("-","a").replace("_","b");
    }
}
