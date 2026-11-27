# BlazeJ2ME

A single-file browser runtime for Java ME/MIDlet compatibility research.

## Purpose

BlazeJ2ME explores how classic CLDC/MIDP applications can be loaded, interpreted and presented in a modern browser without requiring a local Java runtime.

## Features

- JAR/JAD loading and MIDlet discovery;
- Java class/runtime interpretation for supported bytecode;
- MIDP-style display, keypad and soft-key handling;
- RMS-style browser persistence;
- configurable screen, renderer, scheduling and input profiles;
- runtime diagnostics and built-in self-test tooling;
- selected Nokia-style UI/audio compatibility work;
- offline single-file operation.

## Architecture / Technology

The research build is a self-contained HTML application using JavaScript, Canvas/WebGL presentation paths, browser storage and an embedded DEFLATE implementation. The embedded Pako component retains its MIT license notice inside the application source.

## Usage

Open [index.html](index.html) for the project landing page, then choose **Launch Research Build**.

The runnable research build is [app.html](app.html). A synthetic interface-only demonstration is available at [preview.html](preview.html).

No commercial JAR/JAD files are included. Use only applications you are entitled to run.

## Validation

**Current public build:** v1.6 universal compatibility fix.

- recovered as an actual runnable HTML artifact;
- confidentiality scan found no employer/client identifiers, personal records or production credentials;
- both inline JavaScript blocks pass parser validation;
- bundled third-party license notice is preserved.

A full browser compatibility matrix has not yet been completed.

## Known Limitations

Compatibility depends on the target MIDP/CLDC profile, vendor-specific APIs, media/3D requirements, unusual bytecode behavior and browser implementation details. It is not a complete hardware/device emulator.

## Future Work

- repeatable compatibility testing with redistributable/homebrew MIDlets;
- broader media and 3D API coverage;
- regression fixtures for input, persistence and vendor extensions;
- browser performance testing on low-end hardware.

## Project Status

**EXPERIMENTAL — runnable research build; broad compatibility validation pending.**
