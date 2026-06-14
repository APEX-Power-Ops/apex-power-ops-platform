# Power Test Converters

This package contains bounded field-file converters for power test workflows.

Current scope:

- read Omicron Primary Test Manager `.ptm` packages
- extract transformer nameplate, bushing designations, job/session metadata, and transformer test measurements
- write a Doble-style `.dtax` `DataModel-R2` XML file for two-winding transformers

Current emitted test sections:

- overall power factor
- transformer turns ratio
- winding resistance in Doble's M7 winding-resistance containers
- excitation current

Bushing collar measurements are parsed into the source model but are not emitted yet because the available Doble sample did not include populated bushing-test rows to verify that target schema.

## CLI

```powershell
$env:PYTHONPATH='packages/power-test-converters/src'
python packages\power-test-converters\src\ptm_to_dtax.py `
  "C:\path\input.ptm" `
  "C:\path\output.dtax" `
  --template-dtax "C:\path\known-good-template.dtax" `
  --overwrite
```

After installation, the console entry point is:

```powershell
ptm-to-dtax "C:\path\input.ptm" "C:\path\output.dtax" --overwrite
```

`--template-dtax` is recommended for files that will be imported back into Doble software. It starts from a known-good Doble-exported `.dtax` skeleton and patches the PTM transformer data into that full structure. Without a template, the converter writes a minimal `DataModel-R2` XML file that is useful for inspection but may be rejected by Doble as incomplete.

## Windows Drag And Drop

Use `ptm-to-dtax-drop.bat` as a Windows drop target:

1. Select one or more `.ptm` files.
2. Drag them onto `packages\power-test-converters\ptm-to-dtax-drop.bat`.
3. The batch file writes each output beside its source as `source-name-converted.dtax`.

The batch file uses the platform `.venv` interpreter when it exists, then falls back to `python` on `PATH`.
If it is copied outside the package folder, set `PTM_DTAX_ROOT` to the repository/package root first.

For best Doble compatibility, provide a known-good template in either of these ways:

- Put a blank/exported Doble file named `doble-template.dtax` beside `ptm-to-dtax-drop.bat`.
- Or set `DTAX_TEMPLATE` to a known-good Doble `.dtax` path before dropping files.
- If no template is set, the batch file also checks for `Blank_X2.dtax` on the current user's Desktop.

Example:

```powershell
$env:DTAX_TEMPLATE='C:\path\known-good-template.dtax'
```

The preferred template is a Doble-saved blank two-winding transformer file with only the minimum fields needed for Doble to save it. In the observed blank template, serial number is `Default`, the transformer session keeps 46 child sections, and `overall-test-set` keeps Doble's 28 placeholder `overall-test` rows. Template mode preserves the Doble-saved session, admin, and test-condition metadata; it patches the transformer identifiers, CCT designation, and supported test rows with PTM readings.

## Validation

```powershell
$env:PYTHONPATH='packages/power-test-converters/src'
python -m pytest packages/power-test-converters/tests -q
```
