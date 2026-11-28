"""Source-level checks for fail-closed ESP configuration persistence."""
from pathlib import Path
import re

from firmware_source_extract import extract_function, mask_non_code

BLAZEPWIFI = Path(__file__).resolve().parents[2]
ESP8266 = BLAZEPWIFI / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
ESP32 = BLAZEPWIFI / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_rejected(label: str, source: str, validator) -> None:
    try:
        validator(source)
    except AssertionError:
        print(f"CONFIG_PERSISTENCE_MUTATION_REJECTED {label}")
        return
    raise AssertionError(f"unsafe configuration persistence mutation accepted: {label}")


def require_failure_gate(source: str, save_name: str) -> None:
    portal = mask_non_code(extract_function(source, "void setupPortal("))
    match = re.search(
        rf"if\s*\(\s*!\s*{re.escape(save_name)}\s*\(\s*\)\s*\)\s*\{{([\s\S]*?)\}}",
        portal,
    )
    require(match is not None, f"setup route must branch on {save_name} failure")
    failure = match.group(1)
    require("denyRemoteControl()" in failure,
            f"{save_name} failure must keep controller outputs denied")
    require(re.search(r"web\.send\s*\(\s*500\s*,", failure) is not None,
            f"{save_name} failure must return an HTTP 500 response")
    require(re.search(r"\breturn\s*;", failure) is not None,
            f"{save_name} failure must stop the handler")
    require("ESP.restart()" not in failure,
            f"{save_name} failure must not reboot")
    successes = [m.start() for m in re.finditer(r"web\.send\s*\(\s*200\s*,", portal)]
    require(len(successes) >= 2, f"{save_name} route must retain GET and save-success responses")
    success = successes[-1]
    restart = portal.find("ESP.restart()", success)
    require(success > match.end() and restart > success,
            f"{save_name} success response/reboot must follow the failure gate")


def assert_esp8266(source: str) -> None:
    begin = mask_non_code(extract_function(source, "bool beginConfigStore()"))
    require(
        "configStoreReady=configEeprom.beginChecked(sizeof(Config));" in begin and
        "return configStoreReady;" in begin,
        "ESP8266 beginConfigStore must propagate the checked wrapper result",
    )

    save = mask_non_code(extract_function(source, "bool saveCfg("))
    require("if(!beginConfigStore()) return false;" in save,
            "ESP8266 saveCfg must stop before writing when storage cannot initialize")
    require("configEeprom.put(0,cfg);" in save,
            "ESP8266 saveCfg must stage the current Config through the checked store")
    require(re.search(
        r"if\s*\(\s*!\s*configEeprom\.commit\s*\(\s*\)\s*\)\s*\{\s*"
        r"configStoreReady\s*=\s*false\s*;\s*return\s+false\s*;\s*\}",
        save,
    ) is not None,
        "ESP8266 saveCfg must propagate commit failure and invalidate store readiness")
    require(re.search(r"\breturn\s+true\s*;", save) is not None,
            "ESP8266 saveCfg must report success only after commit succeeds")

    load = mask_non_code(extract_function(source, "void loadCfg("))
    require(len(re.findall(r"if\s*\(\s*!\s*saveCfg\s*\(\s*\)\s*\)", load)) >= 2,
            "legacy migration and defaults paths must report failed persistence")
    require_failure_gate(source, "saveCfg")


def assert_esp32(source: str) -> None:
    global_source = mask_non_code(source)
    require(re.search(r"\bbool\s+configStoreValid\s*=\s*true", global_source) is not None,
            "ESP32 must track whether the persisted configuration is valid")
    require(re.search(r"\bbool\s+preferencesReady\s*=\s*false", global_source) is not None,
            "ESP32 must track whether Preferences.begin succeeded")

    raw_defaults = extract_function(source, "void useSafeConfigDefaults(")
    defaults = mask_non_code(raw_defaults)
    require("cfg=Config();" in defaults and 'cfg.server="10.0.0.1";' in raw_defaults and
            'cfg.id="vendo-01";' in raw_defaults and "cfg.apPass=String(b);" in raw_defaults,
            "invalid configuration recovery must use documented safe defaults and a fresh setup password")

    raw_load = extract_function(source, "void loadConfig(")
    load = mask_non_code(raw_load)
    begin = raw_load.find('preferencesReady=prefs.begin("blazevendo",false)')
    marker = re.search(
        r"if\s*\(\s*prefs\.isKey\s*\(\s*\"cfgvalid\"\s*\)\s*&&\s*!\s*"
        r"prefs\.getBool\s*\(\s*\"cfgvalid\"\s*,\s*false\s*\)\s*\)",
        raw_load,
    )
    first_read_positions = [
        raw_load.find(token) for token in
        ("prefs.getString(", "prefs.getInt(", "prefs.getUInt(")
        if raw_load.find(token) >= 0
    ]
    require(begin >= 0, "loadConfig must check Preferences.begin")
    require(marker is not None and begin < marker.start(),
            "loadConfig must check the validity marker after opening Preferences")
    require(bool(first_read_positions) and marker.start() < min(first_read_positions),
            "cfgvalid must be checked before reading any persisted configuration fields")
    require(load.count("configStoreValid=false") >= 2,
            "Preferences-open and invalid-marker paths must mark the configuration invalid")
    require(raw_load.count("useSafeConfigDefaults()") >= 2,
            "both invalid-storage paths must discard partial fields and use safe defaults")
    require(re.search(r"if\s*\(\s*!\s*preferencesReady\s*\)\s*\{", load) is not None,
            "Preferences.begin failure must return before field reads")
    require(load.count("return;") >= 2,
            "invalid-storage paths must return before reading partial fields")

    raw_save = extract_function(source, "bool saveConfig(")
    save = mask_non_code(raw_save)
    require(re.search(r"configStoreValid\s*=\s*false", save) is not None,
            "saveConfig must deny network use while a new configuration is being persisted")
    require(re.search(
        r"if\s*\(\s*!\s*preferencesReady\s*\)\s*\{\s*preferencesReady\s*=\s*prefs\.begin\s*\(",
        save,
    ) is not None, "saveConfig must retry Preferences.begin for setup recovery")
    invalid_marker = raw_save.find('prefs.putBool("cfgvalid",false)')
    valid_marker = raw_save.find('prefs.putBool("cfgvalid",true)')
    first_data = min(
        raw_save.find(token) for token in
        ('prefs.putString("ssid"', 'prefs.putInt("coinpin"', 'prefs.putBool("coinlow"',
         'prefs.putUInt("debounce"')
    )
    last_data = raw_save.rfind('prefs.putUInt("groupms"')
    require(invalid_marker >= 0 and invalid_marker < first_data,
            "saveConfig must persist cfgvalid=false before changing any configuration field")
    require(valid_marker > last_data,
            "saveConfig must publish cfgvalid=true only after every configuration write")
    require(re.search(
        r"if\s*\(\s*prefs\.putBool\s*\(\s*\"cfgvalid\"\s*,\s*false\s*\)\s*==\s*0\s*\)\s*return\s+false\s*;",
        raw_save,
    ) is not None, "failure to invalidate the old marker must stop before field writes")
    require(re.search(r"if\s*\(\s*!\s*ok\s*\)\s*return\s+false\s*;", save) is not None,
            "any field-write failure must leave the validity marker false")
    require(re.search(
        r"if\s*\(\s*prefs\.putBool\s*\(\s*\"cfgvalid\"\s*,\s*true\s*\)\s*==\s*0\s*\)\s*return\s+false\s*;",
        raw_save,
    ) is not None, "failure to publish the final valid marker must fail the save")
    require(save.rfind("configStoreValid=true") > valid_marker,
            "network use may resume only after the final valid marker succeeds")

    expected = {"putString": 6, "putInt": 3, "putBool": 5, "putUInt": 2}
    for method, count in expected.items():
        calls = len(re.findall(rf"\bprefs\.{method}\s*\(", save))
        checked = len(re.findall(rf"\bif\s*\(\s*prefs\.{method}\s*\(", save))
        require(calls == count and checked == count,
                f"all {count} Preferences.{method} writes must be checked; found {checked}/{calls}")

    connect = mask_non_code(extract_function(source, "void connectSta("))
    require(re.search(r"if\s*\(\s*!\s*configStoreValid\s*\|\|\s*cfg\.ssid\.isEmpty\s*\(\s*\)\s*\)", connect) is not None,
            "connectSta must not register or connect using an invalid partial configuration")
    loop = mask_non_code(extract_function(source, "void loop("))
    require(re.search(r"if\s*\(\s*!\s*configStoreValid\s*\)\s*\{\s*delay\s*\(\s*2\s*\)\s*;\s*return\s*;\s*\}", loop) is not None,
            "invalid configuration must return from loop before reconnect or polling")
    require("if(WiFi.status()!=WL_CONNECTED" in loop,
            "network reconnect condition must remain compatible with the shared poll guard")
    require("if(WiFi.status()==WL_CONNECTED" in loop,
            "controller poll condition must remain compatible with the shared poll guard")
    require_failure_gate(source, "saveConfig")


