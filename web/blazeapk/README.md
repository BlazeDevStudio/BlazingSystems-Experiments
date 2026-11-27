# BlazeAPK

A browser-based APK/DEX parsing and Android compatibility-layer experiment.

## Purpose

BlazeAPK studies how selected Java-side Android application structures and behaviors can be inspected and interpreted in a self-contained browser sandbox.

## Features

- APK/ZIP loading and package inspection;
- single- and multi-DEX discovery;
- selected Dalvik bytecode interpretation;
- high-level Android API/HLE experiments;
- resource and layout interpretation;
- Activity lifecycle and input-dispatch experiments;
- browser-local package/session persistence through IndexedDB;
- compatibility diagnostics and built-in self-test support.

## Architecture / Technology

The runtime is a single offline HTML application using JavaScript, IndexedDB and browser-rendered UI/graphics adapters. It provides a constrained compatibility layer rather than a complete Android operating system.

## Usage

Open [index.html](index.html), then choose **Launch Research Build**.

The current runnable research build is [app.html](app.html). A synthetic interface-only demonstration is available at [preview.html](preview.html).

No commercial APK is bundled. Test only software you are entitled to inspect or run.

## Validation

**Current runnable public build:** Beta 0.6.

- recovered as an actual single-file HTML artifact;
- confidentiality scan found no employer/client records, personal data or production credentials;
- inline JavaScript passes parser validation;
- the build includes internal core/self-test code and an embedded redistributable test fixture.

Beta 0.7 documentation was recovered, but no completed Beta 0.7 HTML/package was found in the current Library search, so it is not presented as the active build.

## Known Limitations

BlazeAPK is not a replacement for Android Runtime, AOSP or a device emulator. Native ARM/ARM64 libraries, JNI execution, Binder, full graphics/media stacks, Google Play Services, DRM and many Android framework services are incomplete or unsupported. Compatibility varies widely by application.

## Future Work

- finish the planned Beta 0.7 resource/rendering/input/exception work;
- maintain redistributable regression fixtures;
- expand repeatable browser compatibility tests;
- separate Java-side compatibility scoring from native-library requirements;
- investigate native execution only as a separate research phase.

## Project Status

**EXPERIMENTAL — Beta 0.6 runnable research build; Beta 0.7 remains planned work.**
