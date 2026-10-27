package com.blazesystems.blazenetmonitor;

import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Log;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Small cached HTTPS favicon reader, deliberately separate from live network probes.
 * Fetches the configured site's own publicly linked logo; never queries Google
 * favicon proxies or sends the selected host to a third-party icon API.
 * ICO-only/SVG-only websites fall back to a generic globe icon.
 */
final class TargetFavicons {
    private static final String TAG="BlazeNetMonitor.TargetIcon";
    private static final Pattern LINK=Pattern.compile(
        "<link\\b[^>]*>",Pattern.CASE_INSENSITIVE);
    private static final Pattern ATTR=Pattern.compile(
        "([a-zA-Z-]+)\\s*=\\s*([\\\"'])(.*?)\\2",Pattern.CASE_INSENSITIVE|Pattern.DOTALL);
    private final ExecutorService worker=Executors.newSingleThreadExecutor();
    private final String[] domains={"",""};
    private final Bitmap[] icons=new Bitmap[2];
    private final long[] lastTry={0,0};
    private boolean stopped=false;

    synchronized Bitmap icon(int i){return icons[i];}

    synchronized void shutdown(){
        stopped=true;worker.shutdownNow();
        for(int i=0;i<2;i++) {if(icons[i]!=null)icons[i].recycle();icons[i]=null;}
    }

    void refresh(SharedPreferences preferences,Runnable onUpdated){
        for(int i=0;i<2;i++) {
            final int index=i;
            String address=preferences.getString("target"+index,index==0?
                "https://www.google.com":"https://www.cloudflare.com");
            final String domain=publicHostname(address);
            synchronized(this){
                if(stopped) return;
                long now=android.os.SystemClock.elapsedRealtime();
                if(domain.equals(domains[index]) && now-lastTry[index]<300_000)continue;
                domains[index]=domain;
                lastTry[index]=now;
                icons[index]=null;
            }
            if(domain.isEmpty()){onUpdated.run();continue;}
            worker.execute(()->{
                Bitmap decoded=null;
                try{decoded=findLogo(domain);}catch(Exception e){
                    Log.d(TAG,"Could not load favicon: "+e.getClass().getSimpleName());
                }
                synchronized(this){
                    if(stopped||!domain.equals(domains[index]))return;
                    icons[index]=decoded;
                }
                onUpdated.run();
            });
        }
    }

    static String publicHostname(String raw){
        try{
            String input=raw==null?"":raw.trim();
            if(input.isEmpty())return "";
            URI uri=new URI(input.contains("://")?input:"https://"+input);
            if(!"https".equalsIgnoreCase(uri.getScheme()))return "";
            String host=uri.getHost();
            if(host==null) return "";
            host=host.toLowerCase(Locale.ROOT);
            if(host.length()>253||host.endsWith(".local")||host.endsWith(".internal")||
                host.equals("localhost")||!host.contains(".")||
                host.matches("\\d+\\.\\d+\\.\\d+\\.\\d+"))return "";
            if(!host.matches("[a-z0-9.-]+"))return "";
            return host;
        }catch(Exception e){return "";}
    }

    private static Bitmap findLogo(String host) throws Exception {
        URL root=new URL("https://"+host+"/");
        for(String name:new String[]{"apple-touch-icon.png","favicon.png","favicon-32x32.png"}) {
            Bitmap b=downloadBitmap(new URL(root,name));if(b!=null)return b;
        }
        byte[] html=download(root,98304);
        if(html==null)return null;
        String head=new String(html,java.nio.charset.StandardCharsets.UTF_8);
        int end=head.toLowerCase(Locale.ROOT).indexOf("</head>");
        if(end>0)head=head.substring(0,end);
        Matcher links=LINK.matcher(head);
        int attempts=0;
        while(links.find()&&attempts<8) {
            Matcher attrs=ATTR.matcher(links.group());
            String rel="",href="",type="";
            while(attrs.find()){
                String key=attrs.group(1).toLowerCase(Locale.ROOT);
                if(key.equals("rel"))rel=attrs.group(3).toLowerCase(Locale.ROOT);
                if(key.equals("href"))href=attrs.group(3);
                if(key.equals("type"))type=attrs.group(3).toLowerCase(Locale.ROOT);
            }
            if(!rel.contains("icon")||href.isEmpty()||
                href.toLowerCase(Locale.ROOT).contains(".svg")||
                type.contains("svg"))continue;
            URL url=new URL(root,href);
            if(!"https".equalsIgnoreCase(url.getProtocol()))continue;
            attempts++;
            Bitmap logo=downloadBitmap(url);
            if(logo!=null)return logo;
        }
        return null;
    }

    private static Bitmap downloadBitmap(URL url) {
        try{
            byte[] data=download(url,131072);
            if(data==null)return null;
            Bitmap source=BitmapFactory.decodeByteArray(data,0,data.length);
            if(source==null)return null;
            Bitmap b=Bitmap.createScaledBitmap(source,64,64,true);
            if(source!=b)source.recycle();
            return b;
        }catch(Exception ignored){return null;}
    }

    private static byte[] download(URL url,int limit) throws Exception {
        for(int hop=0;hop<3;hop++){
            if(!"https".equalsIgnoreCase(url.getProtocol()))return null;
            HttpURLConnection c=(HttpURLConnection)url.openConnection();
            c.setConnectTimeout(1800);c.setReadTimeout(1800);
            c.setInstanceFollowRedirects(false);
            c.setRequestProperty("User-Agent","BlazeNetMonitor-Android/0.1");
            try{
                int code=c.getResponseCode();
                if(code>=300&&code<400){
                    String dest=c.getHeaderField("Location");
                    if(dest==null)return null;
                    url=new URL(url,dest);continue;
                }
                if(code!=200||c.getContentLengthLong()>limit)return null;
                ByteArrayOutputStream out=new ByteArrayOutputStream();
                try(InputStream in=c.getInputStream()){
                    byte[] buf=new byte[4096];
                    int n;
                    while((n=in.read(buf))!=-1){
                        if(out.size()+n>limit)return null;
                        out.write(buf,0,n);
                    }
                }
                return out.toByteArray();
            }finally{c.disconnect();}
        }
        return null;
    }
}
