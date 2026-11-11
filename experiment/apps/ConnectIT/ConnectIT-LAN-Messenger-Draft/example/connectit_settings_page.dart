// Draft independent screen; do not merge until LAN Messenger v0.3.1 stability gates pass.
import 'package:flutter/material.dart';
import '../lib/connectit/mini_seed_policy.dart';

class ConnectITSettingsPage extends StatefulWidget {
  const ConnectITSettingsPage({super.key});
  @override
  State<ConnectITSettingsPage> createState() => _ConnectITSettingsPageState();
}
class _ConnectITSettingsPageState extends State<ConnectITSettingsPage> {
  bool enabled = false, wifiOnly = true, cellular = false, background = false;
  @override
  Widget build(BuildContext context) {
    const cyan = Color(0xFF09AFC1);
    final policy = MiniSeedPolicy(enabled: enabled, wifiOnly: wifiOnly,
      allowCellular: cellular, allowBackground: background);
    return Scaffold(
      appBar: AppBar(title: const Text('ConnectIT'), backgroundColor: const Color(0xFF0B2042),
        foregroundColor: Colors.white),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const Text('Hybrid messaging', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        const Text('LAN Messenger stays available without a ConnectIT account.'),
        const SizedBox(height: 18),
        const ListTile(title: Text('ConnectIT account'), subtitle: Text('Not connected — authority adapter pending'),
          leading: Icon(Icons.verified_user_outlined)),
        const Divider(),
        SwitchListTile(title: const Text('Mini-seed relay'), value: enabled,
          subtitle: const Text('Opt-in relay of encrypted text only'), activeColor: cyan,
          onChanged: (v) => setState(() => enabled = v)),
        SwitchListTile(title: const Text('Wi-Fi only'), value: wifiOnly,
          onChanged: enabled ? (v) => setState(() => wifiOnly = v) : null),
        SwitchListTile(title: const Text('Allow cellular data'), value: cellular,
          onChanged: enabled ? (v) => setState(() => cellular = v) : null),
        SwitchListTile(title: const Text('Allow eligible background operation'), value: background,
          subtitle: const Text('Android may restrict or stop background services'),
          onChanged: enabled ? (v) => setState(() => background = v) : null),
        ListTile(title: const Text('Bandwidth limit'), subtitle: Text('${policy.maxKilobytesPerSecond} KiB/s')),
        ListTile(title: const Text('Cache limit'), subtitle: Text('${policy.maxCacheMiB} MiB')),
        const Divider(),
        const ListTile(leading: Icon(Icons.lock_outline), title: Text('SecureBind'),
          subtitle: Text('4-hour approval window, local PIN confirmation before signing')),
        const ListTile(leading: Icon(Icons.link_off), title: Text('Direct transfers only'),
          subtitle: Text('Files and calls fail clearly when direct connectivity fails')),
      ]),
    );
  }
}
