package com.blazesystems.blazenetmonitor;

import android.Manifest;
import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.view.*;
import android.widget.*;
import java.util.Locale;

/**
 * Native Blaze Systems screen. No WebView, accessibility automation,
 * VPN traffic interception, or invented per-app network accounting.
 */
public final class MainActivity extends Activity {
    private static final int NAVY=Color.rgb(7,19,39), PANEL=Color.rgb(14,34,61),
        BLUE=Color.rgb(0,102,255), WHITE=Color.rgb(232,242,255), MUTED=Color.rgb(146,173,201);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private android.content.SharedPreferences pref;
    private TextView down,up,session,day,month,networkState,monitorButton;
    private final TextView[] status=new TextView[2],targetInfo=new TextView[2];
    private final ImageView[] targetLogos=new ImageView[2];
    private final TargetFavicons logos=new TargetFavicons();
    private SpeedGraph graph;
    private Spinner graphType,unit;
    private boolean activeUi;
    private final Runnable refresh=new Runnable(){
        @Override public void run(){
            if(!activeUi)return;
            update();
            ui.postDelayed(this,1000);
        }
    };
    private int dp(float v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private GradientDrawable background(int color,int stroke,int radius){
        GradientDrawable bg=new GradientDrawable();bg.setColor(color);bg.setCornerRadius(dp(radius));
        if(stroke!=0)bg.setStroke(dp(1),stroke);return bg;
    }
    private TextView text(String content,int sp,int color){
        TextView t=new TextView(this);t.setText(content);t.setTextSize(sp);t.setTextColor(color);
        t.setGravity(Gravity.CENTER_VERTICAL);
        return t;
    }
    private LinearLayout column(){
        LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }
    private void add(LinearLayout parent,View child,int height){
        parent.addView(child,new LinearLayout.LayoutParams(-1,height<0?height:dp(height)));
    }
    private LinearLayout card(LinearLayout parent){
        LinearLayout c=column();c.setPadding(dp(16),dp(14),dp(16),dp(16));
        c.setBackground(background(PANEL,Color.rgb(27,63,104),16));
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.bottomMargin=dp(13);
        parent.addView(c,p);return c;
    }
    private TextView action(String label,LinearLayout row,Runnable click){
        TextView button=text(label,13,WHITE);button.setGravity(Gravity.CENTER);
        button.setPadding(dp(10),dp(11),dp(10),dp(11));
        button.setBackground(background(BLUE,0,10));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(46),1);lp.rightMargin=dp(7);
        row.addView(button,lp);button.setOnClickListener(v->click.run());return button;
    }
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        getWindow().setStatusBarColor(NAVY);getWindow().setNavigationBarColor(NAVY);
        pref=getSharedPreferences("settings",0);
        ScrollView scroller=new ScrollView(this);scroller.setFillViewport(true);scroller.setBackgroundColor(NAVY);
        LinearLayout body=column();body.setPadding(dp(16),dp(20),dp(16),dp(32));scroller.addView(body);
        setContentView(scroller);
        TextView title=text("◉  BlazeNetMonitor",24,WHITE);
        title.setTypeface(null,1);add(body,title,41);
        add(body,text("ANDROID  ·  PREVIEW 0.1.5",11,MUTED),24);
        LinearLayout speed=card(body);
        add(speed,text("DEVICE-WIDE NETWORK SPEED",12,MUTED),26);
        down=text("↓  —",25,Color.rgb(52,195,255));down.setTypeface(null,1);add(speed,down,44);
        up=text("↑  —",25,Color.rgb(255,157,59));up.setTypeface(null,1);add(speed,up,44);
        networkState=text("Samples include Wi-Fi, mobile and other interfaces.",11,MUTED);
        add(speed,networkState,43);

        LinearLayout controls=card(body);
        LinearLayout row=new LinearLayout(this);
        add(controls,row,46);
        monitorButton=action("Start monitoring",row,()->{
            if(MonitorService.ACTIVE)stopMonitor();else startMonitor();
        });
        add(controls,text("Pull down notifications for At a glance. Expand the card for both targets and data totals.",11,MUTED),61);

        LinearLayout panel=card(body);
        add(panel,text("LIVE GRAPH",13,WHITE),29);
        graph=new SpeedGraph(this);add(panel,graph,168);
        add(panel,text("Drawing style",12,MUTED),26);
        graphType=new Spinner(this);
        String[] types={"Smooth","Line","Filled","Bars","Steps","Dots","Impulse"};
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,types);
        graphType.setAdapter(adapter);
        String selected=pref.getString("graph","Smooth");
        for(int i=0;i<types.length;i++)if(types[i].equals(selected))graphType.setSelection(i);
        graphType.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,View v,int pos,long id){
                pref.edit().putString("graph",types[pos]).apply();
                update();
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> p){}
        });
        add(panel,graphType,48);

        LinearLayout totals=card(body);
        add(totals,text("TOTALS · DEVICE TRAFFIC",13,WHITE),27);
        session=text("Session  —",14,WHITE);day=text("Today  —",14,WHITE);month=text("This month  —",14,WHITE);
        add(totals,session,31);add(totals,day,31);add(totals,month,31);
        add(totals,text("Session resets when the monitoring process restarts. " +
            "Daily and monthly totals count only while monitoring.",11,MUTED),57);

        LinearLayout checks=card(body);
        add(checks,text("CONNECTION HEALTH",13,WHITE),32);
        for(int i=0;i<2;i++){
            final int j=i;
            LinearLayout targetRow=new LinearLayout(this);targetRow.setGravity(Gravity.CENTER_VERTICAL);
            targetLogos[i]=new ImageView(this);
            targetLogos[i].setImageResource(R.drawable.ic_target_globe);
            targetLogos[i].setScaleType(ImageView.ScaleType.FIT_CENTER);
            LinearLayout.LayoutParams logoSize=new LinearLayout.LayoutParams(dp(24),dp(24));
            logoSize.rightMargin=dp(10);
            targetRow.addView(targetLogos[i],logoSize);
            LinearLayout cell=column();
            status[i]=text("● Target "+(i+1)+"   Waiting",15,WHITE);
            targetInfo[i]=text("No sample",11,MUTED);
            add(cell,status[i],26);add(cell,targetInfo[i],26);
            targetRow.addView(cell,new LinearLayout.LayoutParams(0,dp(56),1));
            action("Edit",targetRow,()->editTarget(j));
            add(checks,targetRow,65);
        }
        add(checks,text("Reachability is a system reachability test; on Android it may not use raw ICMP.",11,MUTED),48);

        LinearLayout settings=card(body);
        add(settings,text("DISPLAY",13,WHITE),29);
        unit=new Spinner(this);
        String[] unitNames={"Bits (Mbps / Kbps)","Bytes (MB/s / KB/s)"};
        unit.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,unitNames));
        unit.setSelection(pref.getBoolean("bits",true)?0:1);
        unit.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,View v,int pos,long id){
                pref.edit().putBoolean("bits",pos==0).apply();update();
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> p){}
        });
        add(settings,unit,50);
        add(settings,text("Top-app usage is not yet available: Android restricts access to other apps' traffic history.",11,MUTED),54);

        LinearLayout about=card(body);
        add(about,text("BLAZE SYSTEMS",13,WHITE),33);
        add(about,text("BlazeNetMonitor Android  ·  0.1.5 preview",12,MUTED),31);
        LinearLayout links=new LinearLayout(this);add(about,links,47);
        action("Support",links,this::showSupport);
        action("Developer Facebook",links,()->open("https://fb.me/manrealloumer"));
        LinearLayout diagnostics= new LinearLayout(this);
        add(about,diagnostics,46);
        action("Crash diagnostics",diagnostics,this::showCrashDiagnostics);

        if(!pref.getBoolean("welcomeDonation",false)){
            pref.edit().putBoolean("welcomeDonation",true).apply();
            ui.postDelayed(this::showSupport,600);
        }
    }
    private void startMonitor(){
        if(Build.VERSION.SDK_INT>=33 &&
           checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED){
            // The user specifically wants the status-bar icon and notification.
            // Do not silently monitor without permission to display them.
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},41);
            return;
        }
        launchMonitor();
    }
    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] results){
        super.onRequestPermissionsResult(requestCode,permissions,results);
        if(requestCode!=41)return;
        if(results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED){
            launchMonitor();
        }else{
            Toast.makeText(this,"Enable notifications to show BlazeNetMonitor in the status bar.",
                Toast.LENGTH_LONG).show();
        }
    }
    private void launchMonitor(){
        try {
            startForegroundService(new Intent(this,MonitorService.class)
                .setAction(MonitorService.ACTION_START));
        }catch(Exception e){
            Toast.makeText(this,"Could not start monitoring: "+e.getMessage(),
                Toast.LENGTH_LONG).show();
        }
        ui.postDelayed(()->{
            update();
            if(!MonitorService.ACTIVE){
                String problem=pref.getString("service_start_error","");
                if(!problem.isEmpty()){
                    networkState.setText("Monitoring unavailable: "+problem);
                    Toast.makeText(this,"Could not start monitoring. "+problem,
                        Toast.LENGTH_LONG).show();
                }
            }
        },1700);
    }
    private void stopMonitor(){
        stopService(new Intent(this,MonitorService.class));update();
    }
    private void update(){
        if(down==null||up==null)return;
        boolean bits=pref.getBoolean("bits",true);
        MonitorState.Frame frame=MonitorState.INSTANCE.frame();
        down.setText("↓  "+TrafficMath.speed(frame.rx,bits));
        up.setText("↑  "+TrafficMath.speed(frame.tx,bits));
        session.setText("Session      ↓ "+TrafficMath.data(frame.sessionRx)+"    ↑ "+TrafficMath.data(frame.sessionTx));
        day.setText("Today         ↓ "+TrafficMath.data(frame.dayRx)+"    ↑ "+TrafficMath.data(frame.dayTx));
        month.setText("This month  ↓ "+TrafficMath.data(frame.monthRx)+"    ↑ "+TrafficMath.data(frame.monthTx));
        graph.data(frame,pref.getString("graph","Smooth"));
        monitorButton.setText(MonitorService.ACTIVE?"Stop monitoring":"Start monitoring");
        for(int i=0;i<2;i++){
            String q=frame.status[i];
            int color=q.equals("Green")?0xff52D68A:q.equals("Yellow")?0xffffd26f:
                q.equals("Orange")?0xffff9d3b:q.equals("Red")?0xffff6e76:MUTED;
            status[i].setText("● Target "+(i+1)+"   "+q);
            status[i].setTextColor(color);targetInfo[i].setText(frame.detail[i]);
        }
        String serviceError=pref.getString("service_start_error","");
        networkState.setText(MonitorService.ACTIVE?
            "● Monitoring · Swipe down for At a glance":
            serviceError.isEmpty()?"Paused · Tap Start monitoring":
                "Monitoring unavailable · "+serviceError);
    }
    private void editTarget(int index){
        LinearLayout box=column();box.setPadding(dp(20),dp(4),dp(20),0);
        Spinner protocols=new Spinner(this);String[] kinds={"HTTPS","TCP","DNS","Reachability"};
        protocols.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,kinds));
        String old=pref.getString("protocol"+index,"HTTPS");
        for(int i=0;i<kinds.length;i++)if(kinds[i].equals(old))protocols.setSelection(i);
        EditText addr=new EditText(this);addr.setSingleLine(true);
        addr.setText(pref.getString("target"+index,index==0?"https://www.google.com":"https://www.cloudflare.com"));
        EditText port=new EditText(this);port.setSingleLine(true);
        port.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        port.setText(String.valueOf(pref.getInt("port"+index,443)));
        add(box,protocols,54);add(box,addr,60);add(box,port,58);
        protocols.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(android.widget.AdapterView<?> p,View v,int pos,long id){
                String kind=kinds[pos];port.setVisibility(kind.equals("TCP")?View.VISIBLE:View.GONE);
                addr.setHint(kind.equals("HTTPS")?"https://www.example.com":"example.com");
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> p){}
        });
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Target "+(index+1))
            .setView(box).setNegativeButton("Cancel",null).setPositiveButton("Save",null).create();
        dialog.setOnShowListener(v->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w->{
            String kind=protocols.getSelectedItem().toString(),url=addr.getText().toString().trim();
            int tcp=443;
            try{tcp=Integer.parseInt(port.getText().toString());}catch(Exception ignored){}
            boolean valid=!url.isEmpty()&&url.length()<2048&&!url.contains(" ");
            if(kind.equals("HTTPS"))valid=valid&&url.startsWith("https://")&&!url.contains("@");
            else valid=valid&&!url.contains("/");
            if(tcp<1||tcp>65535)valid=false;
            if(!valid){addr.setError("Enter a valid "+kind+" target");return;}
            pref.edit().putString("protocol"+index,kind).putString("target"+index,url)
                .putInt("port"+index,tcp).apply();
            MonitorState.INSTANCE.health(index,"Gray","Checking updated target");
            dialog.dismiss();
            refreshLogos();
        }));
        dialog.show();
    }
    private void showSupport(){
        LinearLayout group=column();group.setPadding(dp(22),0,dp(22),0);
        TextView owner=text("Loumer Cabaluna Manreal",15,WHITE);
        owner.setGravity(Gravity.CENTER);add(group,owner,44);
        DonationQrView qr=new DonationQrView(this);add(group,qr,300);
        TextView desc=text("Any amount is appreciated.",13,WHITE);
        desc.setGravity(Gravity.CENTER);add(group,desc,48);
        new AlertDialog.Builder(this).setTitle("Support BlazeNetMonitor")
            .setView(group).setNegativeButton("Not now",null)
            .setPositiveButton("Open PayPal",(d,w)->open(DonationQrView.PAYPAL)).show();
    }
    private void showCrashDiagnostics(){
        final String report=BlazeApplication.crashReport(this);
        if(report.isEmpty()){
            new AlertDialog.Builder(this).setTitle("Crash diagnostics")
                .setMessage("No recorded app exception. Android can also stop apps without a Java exception.")
                .setPositiveButton("OK",null).show();
            return;
        }
        new AlertDialog.Builder(this).setTitle("Previous crash")
            .setMessage(report.length()>1800?report.substring(0,1800)+"\n…":report)
            .setPositiveButton("Copy diagnostics",(dialog,which)->{
                android.content.ClipboardManager clipboard=
                    (android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                if(clipboard!=null)clipboard.setPrimaryClip(
                    android.content.ClipData.newPlainText("BlazeNetMonitor crash",report));
                Toast.makeText(this,"Copied crash report",Toast.LENGTH_SHORT).show();
            })
            .setNeutralButton("Clear",(dialog,which)->BlazeApplication.clearCrash(this))
            .setNegativeButton("Close",null).show();
    }

    private void open(String url){
        try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}
        catch(Exception e){Toast.makeText(this,"Browser unavailable",Toast.LENGTH_SHORT).show();}
    }
    private void refreshLogos(){
        logos.refresh(pref,()->ui.post(()->{
            if(isFinishing()||isDestroyed())return;
            for(int i=0;i<2;i++){
                android.graphics.Bitmap icon=logos.icon(i);
                if(targetLogos[i]!=null){
                    if(icon!=null)targetLogos[i].setImageBitmap(icon);
                    else targetLogos[i].setImageResource(R.drawable.ic_target_globe);
                }
            }
        }));
    }
    @Override protected void onResume(){
        super.onResume();
        activeUi=true;
        refreshLogos();
        ui.post(refresh);
    }
    @Override protected void onPause(){activeUi=false;ui.removeCallbacks(refresh);super.onPause();}
    @Override protected void onDestroy(){logos.shutdown();super.onDestroy();}
}
