package com.blazesystems.blazerental;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.os.*;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {
    private LinearLayout root;private TextView status,time,detail;private Handler handler=new Handler(Looper.getMainLooper());private Boolean lastPaid=null;
    @Override public void onCreate(Bundle b){super.onCreate(b);Policy.applyManagedPolicy(this);buildUi();new Thread(()->{LeaseClient.sync(this);runOnUiThread(()->{buildUi();refresh();});}).start();handler.post(tick);}
    @Override protected void onResume(){super.onResume();Policy.applyManagedPolicy(this);ensureLocked();refresh();}
    private void buildUi(){
        root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(34,44,34,34);root.setGravity(Gravity.CENTER_HORIZONTAL);root.setBackgroundColor(Color.rgb(7,17,31));
        TextView title=text(24);title.setText("BlazeRental");title.setTextColor(Color.rgb(82,228,255));root.addView(title);
        TextView mode=text(13);mode.setText(Policy.isDeviceOwner(this)?"Managed rental phone":"Manual APK · lower security");root.addView(mode);
        status=text(28);time=text(46);detail=text(15);root.addView(status);root.addView(time);root.addView(detail);
        boolean owner=Policy.isDeviceOwner(this),enrolled=LeaseStore.isEnrolled(this),paid=LeaseStore.isLeaseValid(this);lastPaid=paid;
        if(!owner&&!enrolled)manualSetup();else if(!paid)lockedUi();else paidUi();
        Button sync=new Button(this);sync.setText("Check server");sync.setOnClickListener(v->syncNow());root.addView(sync,new LinearLayout.LayoutParams(-1,-2));
        if(owner){Button admin=new Button(this);admin.setText("Administrator");admin.setOnClickListener(v->adminPrompt());root.addView(admin,new LinearLayout.LayoutParams(-1,-2));}
        setContentView(root);ensureLocked();refresh();
    }
    private void manualSetup(){
        TextView m=text(18);m.setText("Manual setup");root.addView(m);
        EditText server=new EditText(this);server.setHint("BlazePwifi server URL");server.setText(LeaseStore.server(this));server.setSingleLine(true);root.addView(server,new LinearLayout.LayoutParams(-1,-2));
        EditText token=new EditText(this);token.setHint("One-time enrollment token");token.setSingleLine(true);root.addView(token,new LinearLayout.LayoutParams(-1,-2));
        Button save=new Button(this);save.setText("Enroll phone");save.setOnClickListener(v->{String s=server.getText().toString().trim(),t=token.getText().toString().trim();if(s.isEmpty()||t.isEmpty()){Toast.makeText(this,"Server URL and enrollment token are required",Toast.LENGTH_LONG).show();return;}LeaseStore.saveManualEnrollment(this,s,t,"Manual rental phone");syncNow();});root.addView(save,new LinearLayout.LayoutParams(-1,-2));
    }
    private void lockedUi(){
        detail.setText("Insert coin to unlock the apps configured by the operator.");
        Button coin=new Button(this);coin.setText("INSERT COIN");coin.setTextSize(22);coin.setOnClickListener(v->new Thread(()->{String msg=LeaseClient.coinStart(this);runOnUiThread(()->{detail.setText(msg);Toast.makeText(this,msg,Toast.LENGTH_LONG).show();});}).start());
        root.addView(coin,new LinearLayout.LayoutParams(-1,90));
    }
    private void paidUi(){
        detail.setText("Paid session active · choose an allowed app.");List<String> apps=Policy.effectiveAllowedPackages(this);int shown=0;
        for(String pkg:apps){if(pkg.equals(getPackageName()))continue;String label=pkg;try{label=getPackageManager().getApplicationLabel(getPackageManager().getApplicationInfo(pkg,0)).toString();}catch(Exception ignored){}
            Button b=new Button(this);b.setText(label);final String p=pkg;b.setOnClickListener(v->{if(!Policy.launchPackage(this,p))Toast.makeText(this,"App unavailable",Toast.LENGTH_SHORT).show();});root.addView(b,new LinearLayout.LayoutParams(-1,-2));if(++shown>=40)break;}
        if(shown==0){TextView none=text(15);none.setText("No paid apps are currently allowed. Ask the operator to configure this phone.");root.addView(none);}
        Button add=new Button(this);add.setText("Add more time");add.setOnClickListener(v->new Thread(()->{String msg=LeaseClient.coinStart(this);runOnUiThread(()->detail.setText(msg));}).start());root.addView(add,new LinearLayout.LayoutParams(-1,-2));
    }
    private void syncNow(){detail.setText("Checking server…");new Thread(()->{boolean ok=LeaseClient.sync(this);runOnUiThread(()->{Toast.makeText(this,ok?"Updated":"Server unavailable",Toast.LENGTH_SHORT).show();buildUi();});}).start();}
    private void adminPrompt(){
        EditText e=new EditText(this);e.setHint("Phone administrator password");e.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        new AlertDialog.Builder(this).setTitle("Administrator").setView(e).setNegativeButton("Cancel",null).setPositiveButton("Unlock",(d,w)->{if(LeaseStore.verifyAdminPassword(this,e.getText().toString()))Policy.enterAdminSettings(this);else Toast.makeText(this,"Invalid or temporarily locked administrator password",Toast.LENGTH_LONG).show();}).show();
    }
    private TextView text(int sp){TextView t=new TextView(this);t.setTextColor(Color.WHITE);t.setTextSize(sp);t.setGravity(Gravity.CENTER);t.setPadding(4,12,4,12);return t;}
    private void ensureLocked(){if(!Policy.isDeviceOwner(this)||LeaseStore.isAdminWindowActive(this))return;try{ActivityManager a=(ActivityManager)getSystemService(ACTIVITY_SERVICE);if(a!=null&&a.getLockTaskModeState()==ActivityManager.LOCK_TASK_MODE_NONE)startLockTask();}catch(Exception ignored){}}
    private final Runnable tick=new Runnable(){public void run(){refresh();handler.postDelayed(this,1000);}};
    private void refresh(){if(status==null||time==null)return;boolean paid=LeaseStore.isLeaseValid(this);long sec=LeaseStore.remainingMs(this)/1000;status.setText(paid?"Rental active":"Time finished");time.setText(String.format(Locale.US,"%02d:%02d:%02d",sec/3600,(sec/60)%60,sec%60));if(lastPaid!=null&&lastPaid!=paid){buildUi();return;}lastPaid=paid;ensureLocked();}
    @Override protected void onDestroy(){handler.removeCallbacks(tick);super.onDestroy();}
}
