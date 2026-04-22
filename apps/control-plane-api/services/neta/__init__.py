"""
NETA ETT Testing Service — Cascade selection, settings, calculation, and evaluation.

Consumes PostgreSQL views and functions created in Supabase migrations:
  - vw_trip_unit_cascade        → cascade drill-down
  - vw_sensor_calc_context      → sensor calculation context
  - fn_sensor_available_settings → available dropdown values
  - fn_calculate_test_currents   → NETA test current calculator
  - fn_evaluate_test_results     → pass/fail evaluator
"""
