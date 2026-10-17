# Reconciliation log

2026-10-18:
1. Dedicated repository name was not accessible, so project placed in isolated
   `experiments/BlazeHackintosh/` directory of `BlazingSystems-Experiments`.
2. OpenCore upstream v1.0.8 versus Dortania guide front-page 1.0.6 is treated
   as documentation drift; no blind Sample.plist copy.
3. 31 CPU family entries are taxonomy only; no automatic EFI for unverified hardware.
4. Browser security prevents arbitrary PC scanning; browser UI performs manual reference
   checks, while Python scanner performs local read-only discovery.
5. No destructive disk operations, Apple binary redistribution or unverified IMG files.
6. Lucide SVGs are packaged offline under ISC; original CSS handles backgrounds/buttons.
