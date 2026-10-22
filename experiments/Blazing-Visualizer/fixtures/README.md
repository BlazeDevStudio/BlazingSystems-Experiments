# Acceptance fixtures

`synthetic.wav` contains generated harmonic C4, E4 and C-major chord attacks at known source timestamps. `flute.wav` is a sequence of three real staccato flute samples (sounding MIDI 72, 76, 81) from the pinned CC0 VSCO 2 CE sample set. Source ownership, transformations and SHA256 hashes are recorded in each `.expected.json`; the original license is `VSCO-LICENSE.txt`. Generation normalizes samples and removes leading silence above 1% of peak before placing them at 0.3, 1.6 and 2.9 seconds.

The `.f32` arrays and `.reference.json` event lists are produced by the original Spotify Python postprocessor and TFLite runtime, independently of the Kotlin port. They freeze a repeatable compatibility comparison. Raw reference note accuracy and the app's optional audio onset refinement are separate measurements. The tiny fixture set cannot establish accuracy on arbitrary full songs.
