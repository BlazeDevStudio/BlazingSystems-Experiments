# Phone workflow and motion continuation

## Published checkpoint

Source48c229e607e7fdcab2f71c915c7f75102a1e9304, Actions39889541772: clean host build/lint/APK and both API26/API36 jobs passed. Publisher39889541799 passed, including signing/version checks and re-downloading the same release bytes.

Preview2 direct APK: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/blazing-visualizer-v1.0.0-preview.2/Blazing-Visualizer-preview-2.apk

31,769,164bytes; SHA256e12079aecc762a08e7bb15b19f79358ef11e9a7f402e4a35d975a386f8fae3d5. Public debug-only signer is retained. Preview1 has a different signer: export wanted presets before uninstall/reinstall; later previews can update Preview2.

The exact previous sourcebbe88d0 failed both device export/playlist cases and the API26 queue-selection case. The fixes replaced overflowing Practice/Mic chips with accessible48dp icon buttons, made Playlists a visible browser tab, and gave a requested playback source priority until Media3 confirms it. A stale old-media update had been able to cancel a new import/selection. Actual natural-end/repeat-all transitions remain covered.

## Motion reference observations

Earlier read-only inspection recovered the full owner-provided recording (648×1404,60fps,464.696729s). Dense samples showed distinct behaviors:

-64–95s: a complete interval outline plus traveling bright tip; detuning changes/drifts the lobes, with a short flash/expanding halo at a tuning lock. Do not claim that equal-tempered detected music was retuned to an exact just ratio.
-105–124s: a changing spatial chord projection and chord-entry bursts.
-145–177s: fixed polygon gates, struck by one sweeping radial hand. Peak flashes are roughly50–100ms; gate rings roughly250–350ms. These visual subdivisions must be distinguished from irrational equal-tempered frequency ratios.
-150–157s: a rotating hand becomes a radial outline; held outlines settle and note/rate changes reshape them.
-233–237s: multiple source traces share one cursor, retain already drawn history, and reset together at a loop boundary. A short fading tail alone does not reproduce this.

The app implements original deterministic interpretations with outline/trail/reveal modes, projected chord axes, rhythmic gates and radial contours. Literal source/stem separation, the video's scripted lesson/thumbnail choreography, and exact authoring parity are not claimed. Video-to-graph tracing remains deferred.

## Microphone note estimates

LiveNoteTracker uses a rolling4096-sample window at22,050Hz with a1024-sample hop. A Hann spectrum finds separated tonal peaks; harmonic rejection prevents one instrument's overtones from lighting many keys. Up to six simultaneous pitches across32–4200Hz are estimates; YIN provides precise monophonic readings within65–1100Hz. Held notes retain identity and onset. Capture timestamps animate the same main canvas even if music playback is paused or no track is open. Ended-note history is retained briefly for visual release.

The186ms window and5.38Hz bin spacing limit closely spaced low notes. Octave doubling, overlapping harmonics, percussive/noisy audio and mixed instruments remain ambiguous. Synthetic tests do not establish arbitrary-song accuracy or physical-phone microphone latency. No audio is sent to a server or saved by live monitoring.

Next candidate adds focused JVM/native-pixel tests and must pass a new exact-source matrix before publication. Preview2 does not contain these later motion/tracker changes.
