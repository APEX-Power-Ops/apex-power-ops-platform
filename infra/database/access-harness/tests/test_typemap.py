"""Tests for access_harness.typemap -- pure logic, no DB connection."""
import datetime
import decimal

import pytest

from access_harness.typemap import ColumnType, map_description, pg_ddl_type


def test_float_maps_to_double_precision():
    ct = map_description(('Sec2InstClrTime', float, 0, 8, 53, 0, True))
    assert ct.pg_type == 'double precision' and ct.round_trippable is True and ct.nullable is True


def test_unknown_type_falls_back_to_text_not_round_trippable():
    ct = map_description(('Weird', object, 0, 0, 0, 0, True))
    assert ct.pg_type == 'text' and ct.round_trippable is False


def test_currency_decimal_maps_to_numeric_19_4():
    assert map_description(('Price', decimal.Decimal, 0, 8, 19, 4, False)).pg_type == 'numeric(19,4)'


def test_bool_and_datetime_and_bytes():
    assert map_description(('flag', bool, 0, 1, 0, 0, True)).pg_type == 'boolean'
    assert map_description(('ts', datetime.datetime, 0, 8, 0, 0, True)).pg_type == 'timestamp'
    assert map_description(('blob', bytearray, 0, 0, 0, 0, True)).pg_type == 'bytea'


def test_pg_ddl_type_roundtrips_a_mapped_column():
    ct = map_description(('n', int, 0, 4, 10, 0, False))
    assert pg_ddl_type(ct) == 'integer'


# Additional coverage tests
def test_int_maps_to_integer():
    ct = map_description(('MyInt', int, 0, 4, 10, 0, False))
    assert ct.pg_type == 'integer'
    assert ct.round_trippable is True
    assert ct.nullable is False


def test_str_maps_to_text():
    ct = map_description(('MyStr', str, 0, 255, 0, 0, True))
    assert ct.pg_type == 'text'
    assert ct.round_trippable is True


def test_bytes_maps_to_bytea():
    ct = map_description(('raw', bytes, 0, 0, 0, 0, False))
    assert ct.pg_type == 'bytea'
    assert ct.round_trippable is True


def test_column_type_fields_populated():
    ct = map_description(('col', float, 0, 8, 53, 0, True))
    assert ct.access_type == str(float)
    assert ct.nullable is True


def test_pg_ddl_type_text():
    ct = map_description(('s', str, 0, 100, 0, 0, True))
    assert pg_ddl_type(ct) == 'text'


def test_pg_ddl_type_numeric():
    ct = map_description(('d', decimal.Decimal, 0, 8, 19, 4, True))
    assert pg_ddl_type(ct) == 'numeric(19,4)'


def test_pg_ddl_type_fallback_unknown():
    ct = map_description(('x', object, 0, 0, 0, 0, True))
    assert pg_ddl_type(ct) == 'text'
