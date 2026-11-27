package com.example.tokenlauncher

import android.app.*
import android.app.admin.DevicePolicyManager
import android.content.*
import android.graphics.Color
import android.os.Bundle
import android.os.CountDownTimer
import android.view.*
import android.widget.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private lateinit var dpm: DevicePolicyManager
    private lateinit var prefs: android.content.SharedPreferences
    private lateinit var root: LinearLayout
    private lateinit var status: TextView
    private lateinit var timerText: TextView
    private var timer: CountDownTimer? = null
    private val io = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        dpm = getSystemService(DEVICE_POLICY_SERVICE) as DevicePolicyManager
        prefs = getSharedPreferences("config", MODE_PRIVATE)
        buildUi()
        refreshState()
    }

    override fun onResume() {
        super.onResume()
        refreshState()
    }

    private fun buildUi() {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(32,32,32,32)
            setBackgroundColor(Color.rgb(12,12,16))
        }
        status = TextView(this).apply {
            setTextColor(Color.LTGRAY); textSize=18f; gravity=Gravity.CENTER
        }
        timerText = TextView(this).apply {
            setTextColor(Color.WHITE); textSize=48f; gravity=Gravity.CENTER; text="LOCKED"
        }
        val coin = Button(this).apply {
            text="INSERT COIN"; textSize=22f; setOnClickListener { requestToken() }
        }
        val settings = Button(this).apply {
            text="ADMIN / SETUP"; setOnClickListener { setupDialog() }
        }
        root.addView(status, LinearLayout.LayoutParams(-1,0,1f))
        root.addView(timerText, LinearLayout.LayoutParams(-1,0,1f))
        root.addView(coin, LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT))
        root.addView(settings, LinearLayout.LayoutParams(-1,ViewGroup.LayoutParams.WRAP_CONTENT))
        setContentView(root)
    }

    private fun admin() = ComponentName(this, TokenDeviceAdminReceiver::class.java)

    private fun enforceKiosk() {
        try {
            if (dpm.isDeviceOwnerApp(packageName)) {
                dpm.setLockTaskPackages(admin(), arrayOf(packageName))
                dpm.setStatusBarDisabled(admin(), true)
                dpm.setKeyguardDisabled(admin(), true)
                startLockTask()
            }
        } catch (_: Exception) {}
    }

    private fun releaseKiosk() {
        try {
            if (dpm.isDeviceOwnerApp(packageName)) {
                stopLockTask()
                dpm.setStatusBarDisabled(admin(), false)
                dpm.setKeyguardDisabled(admin(), false)
            }
        } catch (_: Exception) {}
    }

    private fun refreshState() {
        val until = prefs.getLong("until",0)
        val remain = until-System.currentTimeMillis()
        if (remain>0) {
            releaseKiosk()
            startCountdown(remain)
        } else {
            enforceKiosk()
            showLocked("Insert a token to continue")
        }
        status.text = if (dpm.isDeviceOwnerApp(packageName))
            (if (remain>0) "TIME REMAINING" else "Device-managed launcher")
        else "Prototype mode — Device Owner not provisioned"
    }

    private fun requestToken() {
        val base = prefs.getString("esp32","http://192.168.4.1")!!.trimEnd('/')
        val key = prefs.getString("tokenKey","") ?: ""
        if (key.isBlank()) {
            showLocked("Token API key is not configured")
            return
        }
        status.text="Checking token box…"
        io.execute {
            var c: HttpURLConnection? = null
            try {
                c=URL("$base/api/token").openConnection() as HttpURLConnection
                c.requestMethod="POST"
                c.connectTimeout=3000
                c.readTimeout=3000
                c.doOutput=true
                c.setRequestProperty("Content-Type","application/x-www-form-urlencoded")
                val body="k="+URLEncoder.encode(key,"UTF-8")
                c.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                val code=c.responseCode
                val stream=if(code in 200..299)c.inputStream else c.errorStream
                val text=stream?.bufferedReader()?.readText().orEmpty()
                if(code !in 200..299) throw IllegalStateException("Token box HTTP $code")
                val seconds=JSONObject(text).optLong("seconds",0)
                runOnUiThread {
                    if(seconds>0){
                        val until=System.currentTimeMillis()+seconds*1000
                        prefs.edit().putLong("until",until).apply()
                        startCountdown(seconds*1000)
                    } else showLocked("No token available")
                }
            } catch(e:Exception) {
                runOnUiThread { showLocked("Token box unavailable") }
            } finally {
                c?.disconnect()
            }
        }
    }

    private fun startCountdown(ms:Long){
        releaseKiosk()
        timer?.cancel()
        timer=object:CountDownTimer(ms,1000){
            override fun onTick(x:Long){ timerText.text=format(x); status.text="TIME REMAINING" }
            override fun onFinish(){
                prefs.edit().putLong("until",0).apply()
                enforceKiosk()
                showLocked("Time expired — insert another token")
            }
        }.start()
    }

    private fun format(ms:Long):String {
        val s=ms/1000
        return "%02d:%02d".format(s/60,s%60)
    }

    private fun showLocked(msg:String){
        timerText.text="LOCKED"
        status.text=msg
    }

    private fun setupDialog(){
        val box=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(32,0,32,0)
        }
        val url=EditText(this).apply {
            setText(prefs.getString("esp32","http://192.168.4.1"))
            hint="ESP32 URL"
        }
        val key=EditText(this).apply {
            setText(prefs.getString("tokenKey",""))
            hint="Token API key"
        }
        box.addView(url)
        box.addView(key)
        AlertDialog.Builder(this)
            .setTitle("Token Box")
            .setView(box)
            .setMessage("Use the same API key configured in the ESP32 firmware.")
            .setPositiveButton("SAVE"){_,_->
                prefs.edit()
                    .putString("esp32",url.text.toString().trim())
                    .putString("tokenKey",key.text.toString())
                    .apply()
                refreshState()
            }
            .setNegativeButton("Cancel",null)
            .show()
    }
}
