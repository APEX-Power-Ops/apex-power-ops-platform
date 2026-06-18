"""Capture-mode import (Chip 10): instrument file -> records datasheet.

Path 2 of the capture-mode contract. Parses an instrument file (via the banked
power-test-converters), maps the readings to a records datasheet's instrument_import
controls, and writes confirmed values to records.form_field_values with provenance.
See reference/records/14-CAPTURE-MODE-IMPORT-SPEC.md.
"""
__version__ = "0.1.0"
