# Token Control Prototype

**Type:** Android + ESP32 device-control research  
**Stage:** Experimental security/integration prototype

A local-network study of time-credit/token control between an Android client and an ESP32 access-point device.

## Research Scope

- local token issuance;
- authenticated administrative actions;
- shared-key request validation;
- Android local-network integration;
- device-owner/kiosk design considerations;
- session-expiry behavior.

## Public Preview

Open `preview.html` for a browser-only simulation of the time-credit workflow. It does not manage a real device and does not contact a network.

## Security Boundary

The prototype uses placeholder credentials in source and is not a production authentication system. A production implementation would require stronger secret provisioning, replay resistance, secure administration, platform-specific kiosk enforcement, and device-level regression testing.

## Development Requirements

Before any real deployment:

1. replace placeholder credentials;
2. protect administrative configuration;
3. validate device-owner/kiosk behavior on supported Android versions;
4. define a secure credential-rotation process;
5. test network loss, reboot, process recreation and session expiry;
6. review the threat model for the intended environment.

Use only on devices you own or are authorized to administer.
