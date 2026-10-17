# Hardware database

`families.json` has 31 taxonomy entries with stable IDs, vendor labels, source references and **Research Only** classification.
This does not claim exact CPU SKU compatibility; CPU SKU matching is currently limited to eight explicit mappings in `../blazehackintosh.py`.
Generation names, frequency, socket or brand resemblance alone cannot prove an EFI will work.

Schema v1 fields:
- `schema_version`, `generated_at_utc`, `references` and `families`;
- each family: `id`, `vendor`, `name`, `classification`, `references`, `validated_efi`.

The engine rejects insufficient, duplicated or falsely validated catalog entries.
Future schemas must add precise CPUID, GPU PCI IDs, firmware requirements, CPU instruction sets,
model-specific evidence, macOS limits, confidence and verified dates before compatibility recommendations can be made.
No generic EFI is bundled.
