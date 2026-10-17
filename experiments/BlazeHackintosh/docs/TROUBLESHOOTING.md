# Scanner troubleshooting

- **Python not found:** install Python 3.10+ and check `python --version`.
- **PowerShell unavailable:** CLI returns null fields instead of attempting repairs;
  execute read-only `Get-CimInstance Win32_Processor` yourself to confirm permissions.
- **Linux GPU list empty:** `lspci` is optional; hardware is not deemed unsupported.
- **CPU shown Unknown:** exact SKU is not among the eight reference mappings;
  no forced approximate EFI mapping is performed.
- **Browser buttons seem limited:** this is deliberately a reference preview.
  Evaluate calculates a research classification; Export saves a locally generated JSON report.
- **No macOS installer:** this milestone intentionally does not download or flash macOS.
Never execute third-party EFI bundles or format internal drives to fix a scanner issue.
