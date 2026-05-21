# Lane 501 Onboarding Design Reframing

This directory holds the read-only discovery and sample artifacts for PM Lane 501.

Artifacts produced here do not write any `seam.*` or `public.*` row. The generator opens the database in read-only mode, logs every SQL statement it issues, re-runs the existing Lane 029 extractor against the R3 Temp Power workbook, and materializes review artifacts for the later Lane 502 implementation lane.

Run:

```powershell
.\.venv\Scripts\python.exe apps\mutation-seam\scripts\lane_501_onboarding_design\generate_lane_501_design_artifacts.py
```

Required environment:

1. `DATABASE_URL`, `SEAM_DATABASE_URL`, or `LANE_501_ONBOARDING_DESIGN_ADMIN_DSN` must point at the governed production database.
2. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Estimator R3 - Project Miner Temp Power Testing.xlsm` must exist.
3. `C:/Users/jjswe/Desktop/Project Miner PM Planning/Miner Temp SLD-AP-BCARRASCO.pdf` should exist so topology labels are captured.

Outputs:

1. `discovery/extractor_output_r3_temp_power_<timestamp>.json`
2. `discovery/data_jsonb_samples_<timestamp>.json`
3. `discovery/no_write_sql_log_<timestamp>.txt`
4. `sample/miner_temp_power_testing_intermediate_<timestamp>.json`
5. `sample/miner_temp_power_testing_reconciliation_<timestamp>.json`
6. `sample/miner_temp_power_testing_reconciliation_<timestamp>.md`

The generated reconciliation JSON includes `report_content_sha256`, defined as the SHA-256 of the canonical JSON serialization of the nested `report_body` object with sorted keys and compact separators. Lane 502 must verify against that same canonicalized `report_body` payload before any admitted write.