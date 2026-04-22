#!/usr/bin/env python3
"""
TCC Access -> PostgreSQL Staging Loader
=======================================
Reads Access CSV exports and loads them into a local Docker PostgreSQL instance.
Schema derived from TCC_Database_Schema_Complete_20251020_083655.xlsx.

Prerequisites:
    pip install psycopg2-binary
    Docker container 'tcc_staging' running on port 5433

Usage:
    python tcc_staging_load.py
"""
import csv
import os
import sys
import time
import psycopg2
from psycopg2 import sql
from pathlib import Path

# ============================================================
# Configuration
# ============================================================
CSV_DIR = r"C:\Users\jjswe\Box\TCC_Master\Access DB\tables"
DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "tcc_staging"
DB_USER = "tcc"
DB_PASS = "tcc_staging"

# ============================================================
# Schema Definition (from Access schema workbook)
# ============================================================

TABLES = {
    "BreakerHierarchy_Flat": {
        "fields": [
            ("BreakerID", "INTEGER", True),
            ("BreakerClass", "VARCHAR(255)", True),
            ("ManufacturerID", "INTEGER", True),
            ("ManufacturerName", "VARCHAR(255)", True),
            ("BreakerType", "VARCHAR(255)", True),
            ("BreakerStyle", "VARCHAR(255)", True),
            ("FrameAmps", "REAL", True),
            ("Ordinal", "INTEGER", True),
            ("TestingStandard", "SMALLINT", True),
            ("IntKa_240V", "REAL", True),
            ("IntKa_480V", "REAL", True),
            ("IntKa_600V", "REAL", True),
            ("SeriesKa_240V", "REAL", True),
            ("SeriesKa_480V", "REAL", True),
            ("SeriesKa_600V", "REAL", True),
        ],
        "pks": [],
    },
    "BreakerICCB": {
        "fields": [
            ("ID", "INTEGER", True),
            ("Mfr_ID", "INTEGER", True),
            ("Type", "VARCHAR(24)", True),
            ("cStandard", "SMALLINT", True),
            ("Acdc", "INTEGER", True),
        ],
        "pks": ["ID", "Mfr_ID", "Type", "Acdc"],
    },
    "BreakerICCBStyles": {
        "fields": [
            ("ID", "INTEGER", True),
            ("BreakerID", "INTEGER", False),
            ("Style", "VARCHAR(24)", False),
            ("Ordinal", "INTEGER", True),
            ("r_cont_current", "REAL", True),
            ("r_int_inst_240", "REAL", True),
            ("r_int_inst_480", "REAL", True),
            ("r_int_inst_600", "REAL", True),
            ("r_int_series_240", "REAL", True),
            ("r_int_series_480", "REAL", True),
            ("r_int_series_600", "REAL", True),
            ("c_testing_std", "SMALLINT", True),
            ("TMT_TCCNumber", "VARCHAR(16)", True),
            ("TMT_Notes", "TEXT", True),
            ("TMT_TripPlug", "INTEGER", True),
            ("TMT_BreakerType", "INTEGER", True),
            ("TMT_ThermalMagnetic", "INTEGER", True),
            ("TMT_Use_SST", "SMALLINT", True),
            ("TMT_SST_Mfr", "VARCHAR(24)", True),
            ("TMT_SST_Type", "VARCHAR(24)", True),
            ("TMT_SST_Style", "VARCHAR(24)", True),
            ("r_iec_inst_220", "REAL", True),
            ("r_iec_inst_230", "REAL", True),
            ("r_iec_inst_240", "REAL", True),
            ("r_iec_inst_380", "REAL", True),
            ("r_iec_inst_400", "REAL", True),
            ("r_iec_inst_415", "REAL", True),
            ("r_iec_inst_440", "REAL", True),
            ("r_iec_inst_500", "REAL", True),
            ("r_iec_inst_550", "REAL", True),
            ("r_iec_inst_690", "REAL", True),
            ("TMT_Thermal", "INTEGER", True),
            ("InstOvrAmps", "REAL", True),
            ("InstOvrMinTolerance", "REAL", True),
            ("InstOvrMaxTolerance", "REAL", True),
            ("InstOvrClrDelayTime", "REAL", True),
            ("InstOvrClrRadius", "REAL", True),
            ("InstOvrOpnDelayTime", "REAL", True),
            ("InstOvrOpnRadius", "REAL", True),
            ("InstOvrNoteText", "TEXT", True),
            ("BrkTimesMechOpening50", "REAL", True),
            ("BrkTimesMechOpening60", "REAL", True),
            ("BrkTimesSTDelayBand50", "REAL", True),
            ("BrkTimesSTDelayBand60", "REAL", True),
            ("NInstOvrAmps", "REAL", True),
            ("NInstOvrMinTolerance", "REAL", True),
            ("NInstOvrMaxTolerance", "REAL", True),
            ("NInstOvrClrDelayTime", "REAL", True),
            ("NInstOvrClrRadius", "REAL", True),
            ("NInstOvrOpnDelayTime", "REAL", True),
            ("NInstOvrOpnRadius", "REAL", True),
            ("r_iec_inst_1000", "REAL", True),
            ("InstOvrClrCurve", "SMALLINT", False),
            ("NInstOvrClrCurve", "SMALLINT", False),
            ("InstOvrClrChar", "SMALLINT", False),
            ("NInstOvrClrChar", "SMALLINT", False),
            ("InstOvrCurveCalcClr", "SMALLINT", False),
            ("NInstOvrCurveCalcClr", "SMALLINT", False),
            ("InstOvrClrEnteredAt", "REAL", True),
            ("NInstOvrClrEnteredAt", "REAL", True),
            ("InstOvrOpenCurve", "SMALLINT", False),
            ("NInstOvrOpenCurve", "SMALLINT", False),
            ("InstOvrOpenChar", "SMALLINT", False),
            ("NInstOvrOpenChar", "SMALLINT", False),
            ("InstOvrCurveCalcOpen", "SMALLINT", False),
            ("NInstOvrCurveCalcOpen", "SMALLINT", False),
            ("InstOvrOpenEnteredAt", "REAL", True),
            ("NInstOvrOpenEnteredAt", "REAL", True),
        ],
        "pks": ["ID", "BreakerID", "Style"],
    },
    "BreakerMCCB": {
        "fields": [
            ("ID", "INTEGER", True),
            ("Mfr_ID", "INTEGER", True),
            ("Type", "VARCHAR(24)", True),
            ("cStandard", "SMALLINT", True),
            ("Acdc", "INTEGER", True),
        ],
        "pks": ["ID", "Mfr_ID", "Type", "Acdc"],
    },
    "BreakerMCCBStyles": {
        "fields": [
            ("ID", "INTEGER", True),
            ("BreakerID", "INTEGER", False),
            ("Style", "VARCHAR(24)", False),
            ("Ordinal", "INTEGER", True),
            ("r_cont_current", "REAL", True),
            ("r_int_inst_240", "REAL", True),
            ("r_int_inst_480", "REAL", True),
            ("r_int_inst_600", "REAL", True),
            ("r_int_series_240", "REAL", True),
            ("r_int_series_480", "REAL", True),
            ("r_int_series_600", "REAL", True),
            ("c_testing_std", "SMALLINT", True),
            ("TMT_TCCNumber", "VARCHAR(16)", True),
            ("TMT_Notes", "TEXT", True),
            ("TMT_TripPlug", "INTEGER", True),
            ("TMT_BreakerType", "INTEGER", True),
            ("TMT_ThermalMagnetic", "INTEGER", True),
            ("TMT_Use_SST", "SMALLINT", True),
            ("TMT_SST_Mfr", "VARCHAR(24)", True),
            ("TMT_SST_Type", "VARCHAR(24)", True),
            ("TMT_SST_Style", "VARCHAR(24)", True),
            ("r_iec_inst_220", "REAL", True),
            ("r_iec_inst_230", "REAL", True),
            ("r_iec_inst_240", "REAL", True),
            ("r_iec_inst_380", "REAL", True),
            ("r_iec_inst_400", "REAL", True),
            ("r_iec_inst_415", "REAL", True),
            ("r_iec_inst_440", "REAL", True),
            ("r_iec_inst_500", "REAL", True),
            ("r_iec_inst_550", "REAL", True),
            ("r_iec_inst_690", "REAL", True),
            ("TMT_Thermal", "INTEGER", True),
            ("InstOvrAmps", "REAL", True),
            ("InstOvrMinTolerance", "REAL", True),
            ("InstOvrMaxTolerance", "REAL", True),
            ("InstOvrClrDelayTime", "REAL", True),
            ("InstOvrClrRadius", "REAL", True),
            ("InstOvrOpnDelayTime", "REAL", True),
            ("InstOvrOpnRadius", "REAL", True),
            ("InstOvrNoteText", "TEXT", True),
            ("BrkTimesMechOpening50", "REAL", True),
            ("BrkTimesMechOpening60", "REAL", True),
            ("BrkTimesSTDelayBand50", "REAL", True),
            ("BrkTimesSTDelayBand60", "REAL", True),
            ("NInstOvrAmps", "REAL", True),
            ("NInstOvrMinTolerance", "REAL", True),
            ("NInstOvrMaxTolerance", "REAL", True),
            ("NInstOvrClrDelayTime", "REAL", True),
            ("NInstOvrClrRadius", "REAL", True),
            ("NInstOvrOpnDelayTime", "REAL", True),
            ("NInstOvrOpnRadius", "REAL", True),
            ("r_iec_inst_1000", "REAL", True),
            ("InstOvrClrCurve", "SMALLINT", False),
            ("NInstOvrClrCurve", "SMALLINT", False),
            ("InstOvrClrChar", "SMALLINT", False),
            ("NInstOvrClrChar", "SMALLINT", False),
            ("InstOvrCurveCalcClr", "SMALLINT", False),
            ("NInstOvrCurveCalcClr", "SMALLINT", False),
            ("InstOvrClrEnteredAt", "REAL", True),
            ("NInstOvrClrEnteredAt", "REAL", True),
            ("InstOvrOpenCurve", "SMALLINT", False),
            ("NInstOvrOpenCurve", "SMALLINT", False),
            ("InstOvrOpenChar", "SMALLINT", False),
            ("NInstOvrOpenChar", "SMALLINT", False),
            ("InstOvrCurveCalcOpen", "SMALLINT", False),
            ("NInstOvrCurveCalcOpen", "SMALLINT", False),
            ("InstOvrOpenEnteredAt", "REAL", True),
            ("NInstOvrOpenEnteredAt", "REAL", True),
        ],
        "pks": ["ID", "BreakerID", "Style"],
    },
    "BreakerPCB": {
        "fields": [
            ("ID", "INTEGER", True),
            ("Mfr_ID", "INTEGER", True),
            ("Type", "VARCHAR(24)", True),
            ("cStandard", "SMALLINT", True),
            ("Acdc", "INTEGER", True),
        ],
        "pks": ["ID", "Mfr_ID", "Type", "Acdc"],
    },
    "BreakerPCBStyles": {
        "fields": [
            ("ID", "INTEGER", True),
            ("BreakerID", "INTEGER", False),
            ("Style", "VARCHAR(24)", False),
            ("Ordinal", "INTEGER", True),
            ("r_cont_current", "REAL", True),
            ("r_int_inst_240", "REAL", True),
            ("r_int_inst_480", "REAL", True),
            ("r_int_inst_600", "REAL", True),
            ("r_int_ninst_240", "REAL", True),
            ("r_int_ninst_480", "REAL", True),
            ("r_int_ninst_600", "REAL", True),
            ("r_int_series_240", "REAL", True),
            ("r_int_series_480", "REAL", True),
            ("r_int_series_600", "REAL", True),
            ("c_testing_std", "SMALLINT", True),
            ("r_iec_inst_220", "REAL", True),
            ("r_iec_inst_230", "REAL", True),
            ("r_iec_inst_240", "REAL", True),
            ("r_iec_inst_380", "REAL", True),
            ("r_iec_inst_400", "REAL", True),
            ("r_iec_inst_415", "REAL", True),
            ("r_iec_inst_440", "REAL", True),
            ("r_iec_inst_500", "REAL", True),
            ("r_iec_inst_550", "REAL", True),
            ("r_iec_inst_690", "REAL", True),
            ("r_iec_ninst_220", "REAL", True),
            ("r_iec_ninst_230", "REAL", True),
            ("r_iec_ninst_240", "REAL", True),
            ("r_iec_ninst_380", "REAL", True),
            ("r_iec_ninst_400", "REAL", True),
            ("r_iec_ninst_415", "REAL", True),
            ("r_iec_ninst_440", "REAL", True),
            ("r_iec_ninst_500", "REAL", True),
            ("r_iec_ninst_550", "REAL", True),
            ("r_iec_ninst_690", "REAL", True),
            ("TMT_Use_SST", "SMALLINT", True),
            ("TMT_SST_Mfr", "VARCHAR(24)", True),
            ("TMT_SST_Type", "VARCHAR(24)", True),
            ("TMT_SST_Style", "VARCHAR(24)", True),
            ("InstOvrAmps", "REAL", True),
            ("InstOvrMinTolerance", "REAL", True),
            ("InstOvrMaxTolerance", "REAL", True),
            ("InstOvrClrDelayTime", "REAL", True),
            ("InstOvrClrRadius", "REAL", True),
            ("InstOvrOpnDelayTime", "REAL", True),
            ("InstOvrOpnRadius", "REAL", True),
            ("InstOvrNoteText", "TEXT", True),
            ("BrkTimesMechOpening50", "REAL", True),
            ("BrkTimesMechOpening60", "REAL", True),
            ("BrkTimesSTDelayBand50", "REAL", True),
            ("BrkTimesSTDelayBand60", "REAL", True),
            ("NInstOvrAmps", "REAL", True),
            ("NInstOvrMinTolerance", "REAL", True),
            ("NInstOvrMaxTolerance", "REAL", True),
            ("NInstOvrClrDelayTime", "REAL", True),
            ("NInstOvrClrRadius", "REAL", True),
            ("NInstOvrOpnDelayTime", "REAL", True),
            ("NInstOvrOpnRadius", "REAL", True),
            ("r_iec_inst_1000", "REAL", True),
            ("r_iec_ninst_1000", "REAL", True),
            ("InstOvrClrCurve", "SMALLINT", False),
            ("NInstOvrClrCurve", "SMALLINT", False),
            ("InstOvrClrChar", "SMALLINT", False),
            ("NInstOvrClrChar", "SMALLINT", False),
            ("InstOvrCurveCalcClr", "SMALLINT", False),
            ("NInstOvrCurveCalcClr", "SMALLINT", False),
            ("InstOvrClrEnteredAt", "REAL", True),
            ("NInstOvrClrEnteredAt", "REAL", True),
            ("InstOvrOpenCurve", "SMALLINT", False),
            ("NInstOvrOpenCurve", "SMALLINT", False),
            ("InstOvrOpenChar", "SMALLINT", False),
            ("NInstOvrOpenChar", "SMALLINT", False),
            ("InstOvrCurveCalcOpen", "SMALLINT", False),
            ("NInstOvrCurveCalcOpen", "SMALLINT", False),
            ("InstOvrOpenEnteredAt", "REAL", True),
            ("NInstOvrOpenEnteredAt", "REAL", True),
        ],
        "pks": ["ID", "BreakerID", "Style"],
    },
    "BreakerStyles_Union_Table_Dedup": {
        "fields": [
            ("BreakerID", "INTEGER", True),
            ("TMT_SST_Mfr", "VARCHAR(255)", True),
            ("TMT_SST_Type", "VARCHAR(255)", True),
            ("TMT_SST_Style", "VARCHAR(255)", True),
        ],
        "pks": [],
    },
    "Breaker_TMTThermalTripAdj": {
        "fields": [
            ("FrameSizeID", "INTEGER", True),
            ("Setting", "INTEGER", True),
            ("Desc", "VARCHAR(12)", True),
        ],
        "pks": ["FrameSizeID", "Setting"],
    },
    "DatSection1GfInvEq": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("Desc", "VARCHAR(24)", True),
            ("InOut", "INTEGER", True),
            ("FdOpEq", "SMALLINT", True),
            ("FdOp1", "REAL", True),
            ("FdOp2", "REAL", True),
            ("FdOp3", "REAL", True),
            ("FdOp4", "REAL", True),
            ("FdOp5", "REAL", True),
            ("FdOp6", "REAL", True),
            ("FdClEq", "SMALLINT", True),
            ("FdCl1", "REAL", True),
            ("FdCl2", "REAL", True),
            ("FdCl3", "REAL", True),
            ("FdCl4", "REAL", True),
            ("FdCl5", "REAL", True),
            ("FdCl6", "REAL", True),
            ("IdOpEq", "SMALLINT", True),
            ("IdOp1", "REAL", True),
            ("IdOp2", "REAL", True),
            ("IdOp3", "REAL", True),
            ("IdOp4", "REAL", True),
            ("IdOp5", "REAL", True),
            ("IdOp6", "REAL", True),
            ("IdClEq", "SMALLINT", True),
            ("IdCl1", "REAL", True),
            ("IdCl2", "REAL", True),
            ("IdCl3", "REAL", True),
            ("IdCl4", "REAL", True),
            ("IdCl5", "REAL", True),
            ("IdCl6", "REAL", True),
            ("FdOpICalc", "SMALLINT", True),
            ("FdClICalc", "SMALLINT", True),
            ("IdOpICalc", "SMALLINT", True),
            ("IdClICalc", "SMALLINT", True),
        ],
        "pks": ["SensorID", "Desc"],
    },
    "DatSection3InvEq": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("Desc", "VARCHAR(24)", True),
            ("InOut", "INTEGER", True),
            ("FdOpEq", "SMALLINT", True),
            ("FdOp1", "REAL", True),
            ("FdOp2", "REAL", True),
            ("FdOp3", "REAL", True),
            ("FdOp4", "REAL", True),
            ("FdOp5", "REAL", True),
            ("FdOp6", "REAL", True),
            ("FdClEq", "SMALLINT", True),
            ("FdCl1", "REAL", True),
            ("FdCl2", "REAL", True),
            ("FdCl3", "REAL", True),
            ("FdCl4", "REAL", True),
            ("FdCl5", "REAL", True),
            ("FdCl6", "REAL", True),
            ("IdOpEq", "SMALLINT", True),
            ("IdOp1", "REAL", True),
            ("IdOp2", "REAL", True),
            ("IdOp3", "REAL", True),
            ("IdOp4", "REAL", True),
            ("IdOp5", "REAL", True),
            ("IdOp6", "REAL", True),
            ("IdClEq", "SMALLINT", True),
            ("IdCl1", "REAL", True),
            ("IdCl2", "REAL", True),
            ("IdCl3", "REAL", True),
            ("IdCl4", "REAL", True),
            ("IdCl5", "REAL", True),
            ("IdCl6", "REAL", True),
            ("FdOpICalc", "SMALLINT", True),
            ("FdClICalc", "SMALLINT", True),
            ("IdOpICalc", "SMALLINT", True),
            ("IdClICalc", "SMALLINT", True),
        ],
        "pks": ["SensorID", "Desc"],
    },
    "DatSection3STOvr": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("OvrAmps", "REAL", True),
            ("OvrOpenSec", "REAL", True),
            ("OvrClearSec", "REAL", True),
            ("OvrTolerLowPct", "REAL", True),
            ("OvrTolerHighPct", "REAL", True),
        ],
        "pks": ["SensorID"],
    },
    "DatSection4InstCurves": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("Class", "INTEGER", True),
            ("Time", "REAL", True),
            ("Amps", "REAL", True),
        ],
        "pks": [],
    },
    "DatSensorMaint": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("SEC4_NAME", "VARCHAR(20)", True),
            ("INST_FUNC", "INTEGER", True),
            ("DS4_TOL_HIGH", "REAL", True),
            ("DS4_TOL_LOW", "REAL", True),
            ("DS4_STEP_SIZE", "REAL", True),
            ("DS4_PICKUP_CALC", "INTEGER", True),
            ("DS4_OVR_CALC", "INTEGER", True),
            ("DS4_OVR_VALUE", "REAL", True),
            ("IDELAY_OPENING", "REAL", True),
            ("IDELAY_CLEARING", "REAL", True),
            ("FR_OPENING", "REAL", True),
            ("FR_CLOSING", "REAL", True),
            ("SEC1GF_NAME", "VARCHAR(20)", True),
            ("SEC1GF_GFF", "INTEGER", True),
            ("DS1GF_TOL_HIGH", "REAL", True),
            ("DS1GF_TOL_LOW", "REAL", True),
            ("DS1GF_SEC3_I2T", "INTEGER", True),
            ("DS1GF_PICKUP_CALC", "INTEGER", True),
            ("DS1GF_STEP_SIZE", "REAL", True),
            ("DS1GF_I2T_VAL", "REAL", True),
            ("DS1Gf_I2T_TYPE", "INTEGER", True),
            ("DS1Gf_PICKUP_MAX", "REAL", True),
            ("DS4_REQ_INST", "SMALLINT", True),
            ("DS4_REQ_STTRIP", "SMALLINT", True),
            ("DS4_OVRTOL_MIN", "REAL", True),
            ("DS4_OVRTOL_MAX", "REAL", True),
            ("DS4_MNMXI_MINCALC", "SMALLINT", True),
            ("DS4_MNMXI_MINVAL", "REAL", True),
            ("DS4_MNMXI_MINUNIT", "SMALLINT", True),
            ("DS4_MNMXI_MAXCALC", "SMALLINT", True),
            ("DS4_MNMXI_MAXVAL", "REAL", True),
            ("DS4_MNMXI_MAXUNIT", "SMALLINT", True),
            ("DS4_MNMXI_MAXAMPS", "REAL", True),
            ("DS4_MNMXI_SEPSETT", "SMALLINT", True),
            ("Sec4InstClrCurve", "INTEGER", True),
            ("Sec4InstClrChar", "INTEGER", True),
            ("Sec4InstClrEnteredAt", "REAL", True),
            ("Sec4InstOpenCurve", "INTEGER", True),
            ("Sec4InstOpenChar", "INTEGER", True),
            ("Sec4InstOpenEnteredAt", "REAL", True),
            ("Sec4InstCurveCalcClr", "INTEGER", True),
            ("Sec4InstCurveCalcOpen", "INTEGER", True),
            ("DS4_MNMXI_ALLOWOUT", "SMALLINT", True),
            ("DS4_BRK_OVR", "SMALLINT", True),
            ("DS4_REQ_INST_CCB", "SMALLINT", True),
            ("DS4_MNMXI_MAXUNIT2", "SMALLINT", True),
            ("GIDELAY_OPENING", "REAL", True),
            ("GIDELAY_CLEARING", "REAL", True),
            ("GFR_OPENING", "REAL", True),
            ("GFR_CLOSING", "REAL", True),
            ("SecGfInstClrCurve", "INTEGER", True),
            ("SecGfInstClrChar", "INTEGER", True),
            ("SecGfInstClrEnteredAt", "REAL", True),
            ("SecGfInstOpenCurve", "INTEGER", True),
            ("SecGfInstOpenChar", "INTEGER", True),
            ("SecGfInstOpenEnteredAt", "REAL", True),
            ("SecGfInstCurveCalcClr", "INTEGER", True),
            ("SecGfInstCurveCalcOpen", "INTEGER", True),
        ],
        "pks": ["SensorID"],
    },
    "DatSensorParms": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("Section", "INTEGER", True),
            ("Index", "INTEGER", True),
            ("Value", "REAL", True),
            ("CurveID", "INTEGER", True),
        ],
        "pks": ["SensorID", "Section", "Index", "CurveID"],
    },
    "DatSensorSec2": {
        "fields": [
            ("CurveID", "INTEGER", True),
            ("SensorID", "INTEGER", True),
            ("CurveName", "VARCHAR(24)", True),
            ("Ordinal", "INTEGER", True),
            ("SETTING_METHOD", "INTEGER", True),
            ("SEC2_LTF", "INTEGER", True),
            ("DS2_TOL_HIGH", "REAL", True),
            ("DS2_TOL_LOW", "REAL", True),
            ("SETTING_VAL", "REAL", True),
            ("SETTING_TYPE", "INTEGER", True),
            ("SLOPE", "REAL", True),
            ("DS2_STEP_SIZE", "REAL", True),
            ("DS2_DLY_PTY", "INTEGER", True),
            ("DS2_FORCE_I2X_OUT", "INTEGER", True),
        ],
        "pks": ["SensorID", "CurveName"],
    },
    "DatSettings": {
        "fields": [
            ("KeyID", "INTEGER", True),
            ("SensorID", "INTEGER", True),
            ("Ordinal", "INTEGER", True),
            ("Description", "VARCHAR(20)", True),
            ("Setting", "REAL", True),
            ("TextParm1", "VARCHAR(20)", True),
        ],
        "pks": ["KeyID", "SensorID", "Ordinal"],
    },
    "EMT": {
        "fields": [
            ("ID", "INTEGER", True),
            ("Mfr_ID", "INTEGER", True),
            ("Type", "VARCHAR(24)", True),
            ("Style", "VARCHAR(24)", True),
            ("TCCNumber", "VARCHAR(16)", True),
            ("Note", "TEXT", True),
            ("TripChar", "INTEGER", True),
            ("TripPlug", "INTEGER", True),
        ],
        "pks": ["ID", "Mfr_ID", "Type", "Style"],
    },
    "Manufacturers": {
        "fields": [
            ("ID", "INTEGER", True),
            ("Mfr_Name", "VARCHAR(24)", True),
        ],
        "pks": ["Mfr_Name"],
    },
    "Switch": {
        "fields": [
            ("ID", "INTEGER", True),
            ("MFr_ID", "INTEGER", True),
            ("Type", "VARCHAR(24)", True),
            ("cStandard", "SMALLINT", True),
        ],
        "pks": ["ID", "MFr_ID", "Type"],
    },
    "SwitchStyles": {
        "fields": [
            ("ID", "INTEGER", True),
            ("BreakerID", "INTEGER", True),
            ("Style", "VARCHAR(24)", True),
            ("Ordinal", "INTEGER", True),
            ("r_asym_ka_0_6", "REAL", True),
            ("r_asym_ka_2_75", "REAL", True),
            ("r_asym_ka_5_5", "REAL", True),
            ("r_asym_ka_8_3", "REAL", True),
            ("r_asym_ka_15_5", "REAL", True),
            ("r_asym_ka_25_8", "REAL", True),
            ("r_asym_ka_38", "REAL", True),
            ("r_asym_ka_48_3", "REAL", True),
            ("r_asym_ka_72_5", "REAL", True),
            ("r_asym_ka_121", "REAL", True),
            ("r_asym_ka_145", "REAL", True),
            ("r_asym_ka_169", "REAL", True),
            ("c_testing_std", "SMALLINT", True),
            ("r_iec_ka_0_69", "REAL", True),
            ("r_iec_ka_3_6", "REAL", True),
            ("r_iec_ka_7_2", "REAL", True),
            ("r_iec_ka_12", "REAL", True),
            ("r_iec_ka_17_5", "REAL", True),
            ("r_iec_ka_24", "REAL", True),
            ("r_iec_ka_27", "REAL", True),
            ("r_iec_ka_36", "REAL", True),
            ("r_iec_ka_52", "REAL", True),
            ("r_iec_ka_72_5", "REAL", True),
            ("r_iec_ka_100", "REAL", True),
            ("r_iec_ka_123", "REAL", True),
            ("r_iec_ka_145", "REAL", True),
            ("r_iec_ka_170", "REAL", True),
            ("r_iec_ka_245", "REAL", True),
            ("r_asym_ka_0_24", "REAL", True),
            ("r_asym_ka_0_48", "REAL", True),
            ("Notes", "TEXT", True),
        ],
        "pks": ["ID", "BreakerID", "Style"],
    },
    "ZSISettings": {
        "fields": [
            ("Category", "INTEGER", True),
            ("ParentId", "INTEGER", True),
            ("Section", "INTEGER", True),
            ("Model", "SMALLINT", True),
            ("OpenTime", "REAL", True),
            ("ClearTime", "REAL", True),
            ("TZSI", "SMALLINT", True),
            ("CommonSignal", "SMALLINT", True),
            ("RelayRestrainingSignal", "SMALLINT", True),
            ("AllowSelfRestrain", "SMALLINT", True),
        ],
        "pks": ["Category", "ParentId", "Section"],
    },
    "Breaker_TMTFrameSizes": {
        "fields": [
            ("ID", "INTEGER", True),
            ("StyleID", "INTEGER", False),
            ("FrameSize", "REAL", True),
            ("FrameDesc", "VARCHAR(24)", False),
            ("Sec1Name", "VARCHAR(32)", True),
            ("Sec1PickupCalc", "INTEGER", True),
            ("Sec2Name", "VARCHAR(32)", True),
            ("Sec2PickupCalc", "INTEGER", True),
            ("Sec2CurrentCalc", "INTEGER", True),
            ("Sec2DiscCont", "INTEGER", True),
            ("Sec2CurveType", "INTEGER", True),
            ("Ordinal", "INTEGER", True),
            ("Sec2StepSize", "REAL", True),
            ("Sec2InstClrCurve", "INTEGER", True),
            ("Sec2InstClrRadius", "REAL", True),
            ("Sec2InstClrTime", "REAL", True),
            ("Sec2InstClrChar", "INTEGER", True),
            ("Sec2InstOpenRadius", "REAL", True),
            ("Sec2InstOpenTime", "REAL", True),
            ("Sec2InstEnteredAt", "REAL", True),
            ("Sec2InstOpenCurve", "INTEGER", True),
            ("Sec2InstOpenEnteredAt", "REAL", True),
            ("Sec2InstOpenChar", "INTEGER", True),
            ("Sec2InstCurveCalcClr", "INTEGER", True),
            ("Sec2InstCurveCalcOpen", "INTEGER", True),
            ("Sec2UseOverride", "SMALLINT", False),
        ],
        "pks": ["ID", "StyleID", "FrameDesc"],
    },
    "DatStyle": {
        "fields": [
            ("STYLE_ID", "INTEGER", True),
            ("MFG_ID", "INTEGER", False),
            ("TYPE", "VARCHAR(24)", False),
            ("STYLE", "VARCHAR(24)", False),
            ("NOTES", "TEXT", True),
            ("TCC_NO", "VARCHAR(24)", True),
            ("TCC2_NO", "VARCHAR(24)", True),
            ("SENSOR_NAME", "INTEGER", True),
            ("SENSOR_TYPE", "INTEGER", True),
        ],
        "pks": ["MFG_ID", "TYPE", "STYLE"],
    },
    "EMT_Frames": {
        "fields": [
            ("ID", "INTEGER", True),
            ("StyleID", "INTEGER", False),
            ("FrameSize", "REAL", True),
            ("FrameDesc", "VARCHAR(24)", False),
            ("Ordinal", "INTEGER", True),
        ],
        "pks": ["ID", "StyleID", "FrameDesc"],
    },
    "Breaker_TMTFrameAmps": {
        "fields": [
            ("FrameSizeID", "INTEGER", False),
            ("TripAmp", "REAL", False),
        ],
        "pks": ["FrameSizeID", "TripAmp"],
    },
    "Breaker_TMTFrameCurves": {
        "fields": [
            ("FrameSizeID", "INTEGER", False),
            ("Class", "INTEGER", False),
            ("Time", "REAL", False),
            ("Amps", "REAL", False),
        ],
        "pks": [],
    },
    "Breaker_TMTFrameSettings": {
        "fields": [
            ("FrameSizeID", "INTEGER", False),
            ("fSetting", "REAL", False),
            ("sDesc", "VARCHAR(32)", True),
            ("fLow", "REAL", True),
            ("fHigh", "REAL", True),
        ],
        "pks": ["FrameSizeID", "fSetting"],
    },
    "DatSensor": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("StyleID", "INTEGER", False),
            ("SensorValue", "INTEGER", True),
            ("SensorDesc", "VARCHAR(24)", False),
            ("SensorIdx", "INTEGER", True),
            ("SEC1_NAME", "VARCHAR(20)", True),
            ("SEC1_LTF", "INTEGER", True),
            ("DS1_TOL_HIGH", "REAL", True),
            ("DS1_TOL_LOW", "REAL", True),
            ("DS1_PICKUP_CALC", "INTEGER", True),
            ("MUL_NAME", "VARCHAR(50)", True),
            ("DS1_STEP_SIZE", "REAL", True),
            ("DS1_C_NAME", "VARCHAR(16)", True),
            ("SEC2_NAME", "VARCHAR(20)", True),
            ("SETTING_METHOD", "INTEGER", True),
            ("SEC2_LTF", "INTEGER", True),
            ("DS2_TOL_HIGH", "REAL", True),
            ("DS2_TOL_LOW", "REAL", True),
            ("DS2_STEP_SIZE", "REAL", True),
            ("SETTING_VAL", "REAL", True),
            ("SETTING_TYPE", "INTEGER", True),
            ("SLOPE", "REAL", True),
            ("SEC3_NAME", "VARCHAR(20)", True),
            ("SEC3_STF", "INTEGER", True),
            ("DS3_TOL_HIGH", "REAL", True),
            ("DS3_TOL_LOW", "REAL", True),
            ("DS3_SEC3_I2T", "INTEGER", True),
            ("DS3_PICKUP_CALC", "INTEGER", True),
            ("DS3_STEP_SIZE", "REAL", True),
            ("DS3_I2T_VAL", "REAL", True),
            ("DS3_I2T_TYPE", "INTEGER", True),
            ("SEC4_NAME", "VARCHAR(20)", True),
            ("INST_FUNC", "INTEGER", True),
            ("DS4_TOL_HIGH", "REAL", True),
            ("DS4_TOL_LOW", "REAL", True),
            ("DS4_STEP_SIZE", "REAL", True),
            ("DS4_PICKUP_CALC", "INTEGER", True),
            ("DS4_OVR_CALC", "INTEGER", True),
            ("DS4_OVR_VALUE", "REAL", True),
            ("IDELAY_OPENING", "REAL", True),
            ("IDELAY_CLEARING", "REAL", True),
            ("FR_OPENING", "REAL", True),
            ("FR_CLOSING", "REAL", True),
            ("SEC1GF_NAME", "VARCHAR(20)", True),
            ("SEC1GF_GFF", "INTEGER", True),
            ("DS1GF_TOL_HIGH", "REAL", True),
            ("DS1GF_TOL_LOW", "REAL", True),
            ("DS1GF_SEC3_I2T", "INTEGER", True),
            ("DS1GF_PICKUP_CALC", "INTEGER", True),
            ("DS1GF_STEP_SIZE", "REAL", True),
            ("DS1GF_I2T_VAL", "REAL", True),
            ("DS1Gf_I2T_TYPE", "INTEGER", True),
            ("DS1Gf_PICKUP_MAX", "REAL", True),
            ("DS3_STP_TRACKS", "SMALLINT", True),
            ("DS4_REQ_INST", "SMALLINT", True),
            ("DS4_REQ_STTRIP", "SMALLINT", True),
            ("DS4_OVRTOL_MIN", "REAL", True),
            ("DS4_OVRTOL_MAX", "REAL", True),
            ("DS3_MNMXT_MINCALC", "SMALLINT", True),
            ("DS3_MNMXT_MINVAL", "REAL", True),
            ("DS3_MNMXT_MINUNIT", "SMALLINT", True),
            ("DS3_MNMXT_MAXCALC", "SMALLINT", True),
            ("DS3_MNMXT_MAXVAL", "REAL", True),
            ("DS3_MNMXT_MAXUNIT", "SMALLINT", True),
            ("DS3_MNMXT_MAXAMPS", "REAL", True),
            ("DS4_MNMXI_MINCALC", "SMALLINT", True),
            ("DS4_MNMXI_MINVAL", "REAL", True),
            ("DS4_MNMXI_MINUNIT", "SMALLINT", True),
            ("DS4_MNMXI_MAXCALC", "SMALLINT", True),
            ("DS4_MNMXI_MAXVAL", "REAL", True),
            ("DS4_MNMXI_MAXUNIT", "SMALLINT", True),
            ("DS4_MNMXI_MAXAMPS", "REAL", True),
            ("DS4_MNMXI_SEPSETT", "SMALLINT", True),
            ("Sec4InstClrCurve", "INTEGER", True),
            ("Sec4InstClrChar", "INTEGER", True),
            ("Sec4InstClrEnteredAt", "REAL", True),
            ("Sec4InstOpenCurve", "INTEGER", True),
            ("Sec4InstOpenChar", "INTEGER", True),
            ("Sec4InstOpenEnteredAt", "REAL", True),
            ("Sec4InstCurveCalcClr", "INTEGER", True),
            ("Sec4InstCurveCalcOpen", "INTEGER", True),
            ("DS3_MNMXT_SEPSETT", "SMALLINT", True),
            ("DS3_MNMXT_MAXUNIT2", "SMALLINT", True),
            ("DS3_MNMXT_ALLOWOUT", "SMALLINT", True),
            ("DS4_MNMXI_ALLOWOUT", "SMALLINT", True),
            ("DS4_BRK_OVR", "SMALLINT", True),
            ("DS2_DLY_PTY", "SMALLINT", True),
            ("DS2_OPEN_MINT", "REAL", True),
            ("DS2_CLEAR_MINT", "REAL", True),
            ("InclAD", "SMALLINT", True),
            ("DS4_REQ_INST_CCB", "SMALLINT", True),
            ("DS4_MNMXI_MAXUNIT2", "SMALLINT", True),
            ("DS2_ALLOW_CURVES", "SMALLINT", True),
        ],
        "pks": ["StyleID", "SensorDesc"],
    },
    "EMT_FrameAmps": {
        "fields": [
            ("FrameID", "INTEGER", False),
            ("TripAmp", "REAL", False),
        ],
        "pks": ["FrameID", "TripAmp"],
    },
    "EMT_Sections": {
        "fields": [
            ("ID", "INTEGER", True),
            ("Name", "VARCHAR(24)", True),
            ("FrameID", "INTEGER", True),
            ("SecChar", "INTEGER", True),
            ("CurveType", "INTEGER", True),
            ("PickupCalc", "INTEGER", True),
            ("PickupTolerLow", "REAL", True),
            ("PickupTolerHigh", "REAL", True),
            ("PickupSetting", "INTEGER", True),
            ("StepSize", "REAL", True),
            ("CurrentCalc", "INTEGER", True),
            ("DelayClrCurve", "INTEGER", True),
            ("DelayOpenTime", "REAL", True),
            ("DelayClearTime", "REAL", True),
            ("OpenCurveRadius", "REAL", True),
            ("ClearCurveRadius", "REAL", True),
        ],
        "pks": ["ID", "FrameID", "SecChar"],
    },
    "DatPlugs": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("PlugVal", "INTEGER", True),
        ],
        "pks": ["SensorID", "PlugVal"],
    },
    "DatSection1GfGFD": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("Ordinal", "INTEGER", False),
            ("GFD_DESC", "VARCHAR(24)", True),
            ("GFD_OPEN", "REAL", True),
            ("GFD_CLEAR", "REAL", True),
            ("I_OPEN", "REAL", True),
            ("I_CLEAR", "REAL", True),
            ("T_OPEN", "REAL", True),
            ("T_CLEAR", "REAL", True),
            ("I2X", "SMALLINT", True),
            ("GFD_X", "REAL", True),
            ("GFD_K", "REAL", True),
            ("GFD_SGF", "SMALLINT", True),
            ("GFD_LOWPU", "REAL", True),
            ("GFD_KHI", "REAL", True),
        ],
        "pks": ["SensorID", "Ordinal"],
    },
    "DatSection1GfGFP": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("GFP_DESC", "VARCHAR(24)", True),
            ("GFP_SETTING", "REAL", True),
            ("Mode", "INTEGER", True),
        ],
        "pks": [],
    },
    "DatSection1Mult": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("LTD_C", "REAL", True),
        ],
        "pks": [],
    },
    "DatSection1Sett": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("LTD_SETTING", "REAL", True),
        ],
        "pks": [],
    },
    "DatSection2LTD": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("LTD_DESC", "VARCHAR(24)", True),
            ("LTD_SETTING", "REAL", True),
            ("CurveID", "INTEGER", True),
        ],
        "pks": [],
    },
    "DatSection3STD": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("Ordinal", "INTEGER", True),
            ("STD_DESC", "VARCHAR(24)", True),
            ("STD_OPEN", "REAL", True),
            ("STD_CLEAR", "REAL", True),
            ("I_OPEN", "REAL", True),
            ("I_CLEAR", "REAL", True),
            ("T_OPEN", "REAL", True),
            ("T_CLEAR", "REAL", True),
            ("I2X", "SMALLINT", True),
        ],
        "pks": ["SensorID", "Ordinal"],
    },
    "DatSection3STP": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("STP_DESC", "VARCHAR(24)", True),
            ("STP_SETTING", "REAL", True),
        ],
        "pks": [],
    },
    "DatSection4InstPickup": {
        "fields": [
            ("SensorID", "INTEGER", True),
            ("IP_DESC", "VARCHAR(10)", True),
            ("IP_SETTING", "REAL", True),
            ("Mode", "INTEGER", True),
        ],
        "pks": [],
    },
    "EMT_BandNames": {
        "fields": [
            ("ID", "INTEGER", True),
            ("SecID", "INTEGER", True),
            ("BandName", "VARCHAR(24)", False),
            ("Ordinal", "INTEGER", False),
            ("CurrentAt", "REAL", True),
        ],
        "pks": ["ID", "SecID", "BandName"],
    },
    "EMT_Pickups": {
        "fields": [
            ("SecID", "INTEGER", True),
            ("Setting", "REAL", True),
            ("Description", "VARCHAR(16)", False),
        ],
        "pks": ["SecID", "Setting"],
    },
    "EMT_Curves": {
        "fields": [
            ("ParentID", "INTEGER", True),
            ("Class", "INTEGER", True),
            ("Time", "REAL", False),
            ("Amps", "REAL", False),
        ],
        "pks": [],
    },
}

RELATIONSHIPS = [
    ("Breaker_TMTFrameSizes", "ID", "Breaker_TMTFrameAmps", "FrameSizeID"),
    ("Breaker_TMTFrameSizes", "ID", "Breaker_TMTFrameCurves", "FrameSizeID"),
    ("Breaker_TMTFrameSizes", "ID", "Breaker_TMTFrameSettings", "FrameSizeID"),
    ("BreakerICCBStyles", "ID", "Breaker_TMTFrameSizes", "StyleID"),
    ("BreakerMCCBStyles", "ID", "Breaker_TMTFrameSizes", "StyleID"),
    ("DatSensor", "SensorID", "DatPlugs", "SensorID"),
    ("DatSensor", "SensorID", "DatSection1GfGFD", "SensorID"),
    ("DatSensor", "SensorID", "DatSection1GfGFP", "SensorID"),
    ("DatSensor", "SensorID", "DatSection1Mult", "SensorID"),
    ("DatSensor", "SensorID", "DatSection1Sett", "SensorID"),
    ("DatSensor", "SensorID", "DatSection2LTD", "SensorID"),
    ("DatSensor", "SensorID", "DatSection3STD", "SensorID"),
    ("DatSensor", "SensorID", "DatSection3STP", "SensorID"),
    ("DatSensor", "SensorID", "DatSection4InstPickup", "SensorID"),
    ("DatStyle", "STYLE_ID", "DatSensor", "StyleID"),
    ("EMT_BandNames", "ID", "EMT_Curves", "ParentID"),
    ("EMT_Frames", "ID", "EMT_FrameAmps", "FrameID"),
    ("EMT_Frames", "ID", "EMT_Sections", "FrameID"),
    ("EMT_Sections", "ID", "EMT_BandNames", "SecID"),
    ("EMT_Sections", "ID", "EMT_Pickups", "SecID"),
    ("EMT", "ID", "EMT_Frames", "StyleID"),
    ("Manufacturers", "ID", "DatStyle", "MFG_ID"),
]

LOAD_ORDER = ["BreakerHierarchy_Flat", "BreakerICCB", "BreakerICCBStyles", "BreakerMCCB", "BreakerMCCBStyles", "BreakerPCB", "BreakerPCBStyles", "BreakerStyles_Union_Table_Dedup", "Breaker_TMTThermalTripAdj", "DatSection1GfInvEq", "DatSection3InvEq", "DatSection3STOvr", "DatSection4InstCurves", "DatSensorMaint", "DatSensorParms", "DatSensorSec2", "DatSettings", "EMT", "Manufacturers", "Switch", "SwitchStyles", "ZSISettings", "Breaker_TMTFrameSizes", "DatStyle", "EMT_Frames", "Breaker_TMTFrameAmps", "Breaker_TMTFrameCurves", "Breaker_TMTFrameSettings", "DatSensor", "EMT_FrameAmps", "EMT_Sections", "DatPlugs", "DatSection1GfGFD", "DatSection1GfGFP", "DatSection1Mult", "DatSection1Sett", "DatSection2LTD", "DatSection3STD", "DatSection3STP", "DatSection4InstPickup", "EMT_BandNames", "EMT_Pickups", "EMT_Curves"]


# ============================================================
# Helper Functions
# ============================================================
def connect():
    """Connect to staging PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )

def create_table(cur, table_name, info):
    """Create a staging table with source-faithful naming.
    PK columns are forced NOT NULL regardless of Access metadata."""
    pk_set = set(info["pks"])
    col_defs = []
    for fname, ftype, nullable in info["fields"]:
        # PK columns must be NOT NULL even if Access says nullable
        if fname in pk_set:
            col_defs.append(f'    "{fname}" {ftype} NOT NULL')
        else:
            null_str = "" if nullable else " NOT NULL"
            col_defs.append(f'    "{fname}" {ftype}{null_str}')

    pk_clause = ""
    if info["pks"]:
        pk_list = ", ".join(f'"{c}"' for c in info["pks"])
        pk_clause = f",\n    PRIMARY KEY ({pk_list})"

    ddl = "CREATE TABLE \"{name}\" (\n{cols}{pk}\n);".format(
        name=table_name,
        cols=",\n".join(col_defs),
        pk=pk_clause
    )

    cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
    cur.execute(ddl)

def load_csv(cur, table_name, info, csv_dir):
    """Load a CSV into the staging table using COPY FROM STDIN for speed."""
    csv_path = os.path.join(csv_dir, f"{table_name}.csv")
    if not os.path.exists(csv_path):
        print(f"  WARNING: {csv_path} not found, skipping")
        return 0

    # Read CSV header to map columns
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        csv_header = [h.strip() for h in next(reader)]

    # Case-insensitive column matching
    table_fields = {f[0].lower(): f[0] for f in info["fields"]}
    col_map = []
    for h in csv_header:
        matched = table_fields.get(h.lower())
        col_map.append(matched)  # None if no match

    valid_cols = [c for c in col_map if c is not None]
    valid_indices = [i for i, c in enumerate(col_map) if c is not None]

    if not valid_cols:
        print(f"  WARNING: No matching columns for {table_name}")
        return 0

    unmatched = [csv_header[i] for i, c in enumerate(col_map) if c is None]
    if unmatched:
        print(f"\n    Note: {len(unmatched)} CSV columns not in schema: {unmatched[:5]}{'...' if len(unmatched) > 5 else ''}")

    # Use COPY FROM STDIN with CSV format for bulk speed
    col_list = ", ".join(f'"{c}"' for c in valid_cols)
    copy_sql = f'COPY "{table_name}" ({col_list}) FROM STDIN WITH (FORMAT CSV, NULL \'\')'

    # Build a filtered CSV in memory (only matched columns)
    import io
    buf = io.StringIO()
    row_count = 0

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        writer = csv.writer(buf)
        for row in reader:
            filtered = []
            for idx in valid_indices:
                val = row[idx].strip() if idx < len(row) and row[idx].strip() != "" else ""
                filtered.append(val)
            writer.writerow(filtered)
            row_count += 1

    buf.seek(0)
    try:
        cur.copy_expert(copy_sql, buf)
    except Exception as e:
        # If COPY fails (e.g., type mismatch), fall back to row-by-row INSERT
        cur.connection.rollback()
        print(f"\n    COPY failed ({e}), falling back to INSERT...")
        cur.execute("BEGIN;")
        row_count = _fallback_insert(cur, table_name, valid_cols, valid_indices, csv_path)

    return row_count

def _fallback_insert(cur, table_name, columns, valid_indices, csv_path):
    """Row-by-row INSERT with savepoints for error resilience."""
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    query = f'INSERT INTO "{table_name}" ({col_list}) VALUES ({placeholders})'

    row_count = 0
    error_count = 0
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row_num, row in enumerate(reader, 1):
            values = []
            for idx in valid_indices:
                val = row[idx].strip() if idx < len(row) and row[idx].strip() != "" else None
                values.append(val)
            try:
                cur.execute("SAVEPOINT sp;")
                cur.execute(query, values)
                cur.execute("RELEASE SAVEPOINT sp;")
                row_count += 1
            except Exception as e:
                cur.execute("ROLLBACK TO SAVEPOINT sp;")
                error_count += 1
                if error_count <= 5:
                    print(f"    Row {row_num} error: {e}")
                elif error_count == 6:
                    print(f"    ... suppressing further errors")

    if error_count:
        print(f"    {error_count} rows failed, {row_count} succeeded")
    return row_count

def validate_counts(cur, table_name, expected_source):
    """Check row count matches expectation."""
    cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    actual = cur.fetchone()[0]
    match = "OK" if actual == expected_source else f"MISMATCH (expected {expected_source})"
    return actual, match

# ============================================================
# Expected source row counts (from schema workbook)
# ============================================================
EXPECTED_COUNTS = {
    "Breaker_TMTFrameAmps": 67206,
    "Breaker_TMTFrameCurves": 1143458,
    "Breaker_TMTFrameSettings": 58041,
    "Breaker_TMTFrameSizes": 42238,
    "Breaker_TMTThermalTripAdj": 21790,
    "BreakerHierarchy_Flat": 9090,
    "BreakerICCB": 29,
    "BreakerICCBStyles": 608,
    "BreakerMCCB": 640,
    "BreakerMCCBStyles": 10335,
    "BreakerPCB": 157,
    "BreakerPCBStyles": 3279,
    "BreakerStyles_Union_Table_Dedup": 409,
    "DatPlugs": 49901,
    "DatSection1GfGFD": 72464,
    "DatSection1GfGFP": 65871,
    "DatSection1GfInvEq": 8550,
    "DatSection1Mult": 4832,
    "DatSection1Sett": 128718,
    "DatSection2LTD": 158074,
    "DatSection3InvEq": 22620,
    "DatSection3STD": 139643,
    "DatSection3STOvr": 3,
    "DatSection3STP": 114754,
    "DatSection4InstCurves": 94873,
    "DatSection4InstPickup": 152449,
    "DatSensor": 17831,
    "DatSensorMaint": 2572,
    "DatSensorParms": 136384,
    "DatSensorSec2": 3919,
    "DatSettings": 3514,
    "DatStyle": 2094,
    "EMT": 174,
    "EMT_BandNames": 2978,
    "EMT_Curves": 40808,
    "EMT_FrameAmps": 1704,
    "EMT_Frames": 806,
    "EMT_Pickups": 6593,
    "EMT_Sections": 1768,
    "Manufacturers": 450,
    "Switch": 420,
    "SwitchStyles": 6051,
    "ZSISettings": 7566,
}

# ============================================================
# Main Execution
# ============================================================
def main():
    print("=" * 60)
    print("TCC Access -> PostgreSQL Staging Loader")
    print("=" * 60)
    print(f"CSV source: {CSV_DIR}")
    print(f"Target: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Tables to load: {len(LOAD_ORDER)}")
    print()
    
    conn = connect()
    conn.autocommit = False
    cur = conn.cursor()
    
    # Phase 1: Create all tables (drop order = reverse of load order)
    print("Phase 1: Creating staging tables...")
    drop_order = list(reversed(LOAD_ORDER))
    for table_name in drop_order:
        cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
    conn.commit()
    
    for table_name in LOAD_ORDER:
        info = TABLES[table_name]
        create_table(cur, table_name, info)
        print(f"  Created: {table_name}")
    conn.commit()
    print(f"  {len(LOAD_ORDER)} tables created.
")
    
    # Phase 2: Load CSVs in dependency order
    print("Phase 2: Loading CSV data...")
    results = {}
    total_start = time.time()
    
    for i, table_name in enumerate(LOAD_ORDER, 1):
        info = TABLES[table_name]
        start = time.time()
        print(f"  [{i}/{len(LOAD_ORDER)}] Loading {table_name}...", end=" ", flush=True)
        
        try:
            conn.rollback()  # clean state
            cur.execute("BEGIN;")
            count = load_csv(cur, table_name, info, CSV_DIR)
            conn.commit()
            elapsed = time.time() - start
            results[table_name] = count
            print(f"{count:,} rows ({elapsed:.1f}s)")
        except Exception as e:
            conn.rollback()
            print(f"ERROR: {e}")
            results[table_name] = f"ERROR: {e}"
    
    total_elapsed = time.time() - total_start
    print(f"
  Total load time: {total_elapsed:.1f}s
")
    
    # Phase 3: Validate row counts
    print("Phase 3: Validating row counts...")
    print(f"  {'Table':<40} {'Loaded':>10} {'Expected':>10} {'Status':<15}")
    print(f"  {'-'*40} {'-'*10} {'-'*10} {'-'*15}")
    
    mismatches = 0
    for table_name in LOAD_ORDER:
        expected = EXPECTED_COUNTS.get(table_name, "?")
        if isinstance(results[table_name], int):
            actual, status = validate_counts(cur, table_name, expected if expected != "?" else results[table_name])
            if status != "OK":
                mismatches += 1
            print(f"  {table_name:<40} {actual:>10,} {str(expected):>10} {status:<15}")
        else:
            print(f"  {table_name:<40} {'FAILED':>10} {str(expected):>10} {'ERROR':<15}")
            mismatches += 1
    
    # Phase 4: Check FK integrity (orphan detection)
    print(f"
Phase 4: FK Integrity Checks...")
    for parent, pfield, child, cfield in RELATIONSHIPS:
        if parent in LOAD_ORDER and child in LOAD_ORDER:
            try:
                cur.execute(f'''
                    SELECT COUNT(*) FROM "{child}" c
                    LEFT JOIN "{parent}" p ON c."{cfield}" = p."{pfield}"
                    WHERE p."{pfield}" IS NULL AND c."{cfield}" IS NOT NULL
                ''')
                orphans = cur.fetchone()[0]
                status = "OK" if orphans == 0 else f"{orphans:,} ORPHANS"
                print(f"  {child}.{cfield} -> {parent}.{pfield}: {status}")
            except Exception as e:
                print(f"  {child}.{cfield} -> {parent}.{pfield}: ERROR ({e})")
                conn.rollback()
    
    print(f"
{'='*60}")
    print(f"SUMMARY: {len(LOAD_ORDER)} tables, {mismatches} mismatches")
    total_rows = sum(v for v in results.values() if isinstance(v, int))
    print(f"Total rows loaded: {total_rows:,}")
    print(f"{'='*60}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
