package com.blazesystems.blazenetmonitor;

import android.content.SharedPreferences;
import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.URL;
import java.net.HttpURLConnection;
import java.util.Locale;

/** Target checks never run on Android's main thread. Each has a fixed timeout. */
public final class HealthProbe {
    public static final class Result {
        public final String quality, message;
        Result(String quality,String message){this.quality=quality;this.message=message;}
    }
    private HealthProbe(){}
    public static Result run(SharedPreferences p,int index){
        final String kind=p.getString("protocol"+index,"HTTPS");
        String input=p.getString("target"+index,index==0?"https://www.google.com":"https://www.cloudflare.com").trim();
        long start=System.nanoTime();
        if(input.isEmpty())return new Result("Gray","Not configured");
        try {
            switch(kind){
                case "HTTPS": {
                    URL url=new URL(input);
                    if(!url.getProtocol().equalsIgnoreCase("https")||url.getUserInfo()!=null)
                        return new Result("Red","HTTPS URL required");
                    HttpURLConnection c=(HttpURLConnection)url.openConnection();
                    c.setConnectTimeout(2500);c.setReadTimeout(2500);
                    c.setInstanceFollowRedirects(false);
                    c.setRequestMethod("HEAD");
                    try{int code=c.getResponseCode();if(code<100||code>=600)throw new IOException("Invalid HTTP response");}
                    finally{c.disconnect();}
                    break;
                }
                case "TCP": {
                    int port=p.getInt("port"+index,443);
                    if(port<1||port>65535) return new Result("Red","Invalid TCP port");
                    if(input.contains("/")||input.contains(" "))return new Result("Red","Hostname required");
                    try(Socket s=new Socket()){s.connect(new InetSocketAddress(input,port),2500);}
                    break;
                }
                case "DNS": {
                    if(input.contains("/")||input.contains(" "))return new Result("Red","Domain required");
                    InetAddress.getByName(input);
                    break;
                }
                case "Reachability": {
                    // Android's InetAddress.isReachable may use TCP echo instead of ICMP.
                    // Deliberately do not label this as a validated raw ICMP probe.
                    if(input.contains("/")||input.contains(" "))return new Result("Red","Hostname required");
                    if(!InetAddress.getByName(input).isReachable(2200))
                        throw new IOException("No reachability response");
                    break;
                }
                default:return new Result("Gray","Unsupported protocol");
            }
            long ms=(System.nanoTime()-start)/1_000_000;
            return new Result(ms>350?"Orange":ms>180?"Yellow":"Green",
                String.format(Locale.US,"%s · %d ms",kind,ms));
        }catch(Exception e){
            return new Result("Red",kind+" · Unreachable");
        }
    }
}
