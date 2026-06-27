"""Tests for access_harness.checksum -- pure logic, no DB connection.

ColumnType ctor is positional:
    ColumnType(access_type, pg_type, nullable, size, precision, round_trippable)
"""
from collections import Counter

from access_harness.checksum import canonical_row, multiset_diff, table_checksum
from access_harness.typemap import ColumnType

# A float-typed column (pg_type in {'double precision','real'}).
FT = ColumnType('float', 'double precision', True, None, 53, True)
# A real (single-precision) float column -- also float-formatted.
RT = ColumnType('float', 'real', True, None, 24, True)
# A text/string column.
ST = ColumnType('str', 'text', True, None, None, True)
# An integer column.
IT = ColumnType('int', 'integer', False, None, None, True)

T = [IT, FT]


def test_checksum_is_order_independent():
    assert table_checksum([(1, 1.5), (2, 2.5)], T) == table_checksum([(2, 2.5), (1, 1.5)], T)


def test_checksum_float_round_trip_byte_identical():
    assert canonical_row((0.1 + 0.2,), [FT]) == canonical_row((0.30000000000000004,), [FT])


def test_null_vs_empty_string_distinct():
    assert canonical_row((None,), [ST]) != canonical_row(('',), [ST])


def test_multiset_diff_per_key_counts():
    assert multiset_diff(Counter({'k': 3}), Counter({'k': 1})) == {
        'k': {'access': 3, 'tcc': 1, 'delta': 2}
    }


def test_checksum_changes_when_a_value_changes():
    assert table_checksum([(1, 1.5)], T) != table_checksum([(1, 1.6)], T)


# --- Additional coverage ---------------------------------------------------


def test_canonical_row_null_sentinel_is_fixed():
    assert canonical_row((None,), [ST]) == '\x00NULL'


def test_canonical_row_separator_joins_fixed_order():
    # Columns joined in given order with the 0x01 separator.
    assert canonical_row((1, 1.5), T) == '1\x011.5'


def test_canonical_row_real_type_is_float_formatted():
    # 'real' pg_type also uses .17g formatting.
    assert canonical_row((0.1 + 0.2,), [RT]) == canonical_row((0.30000000000000004,), [RT])


def test_canonical_row_non_float_uses_str():
    # Integer column: plain str(), not .17g.
    assert canonical_row((42,), [IT]) == '42'


def test_table_checksum_is_sha256_hex():
    cs = table_checksum([(1, 1.5)], T)
    assert isinstance(cs, str)
    assert len(cs) == 64
    assert all(c in '0123456789abcdef' for c in cs)


def test_table_checksum_empty_is_deterministic():
    assert table_checksum([], T) == table_checksum([], T)


def test_multiset_diff_keys_only_on_left():
    assert multiset_diff(Counter({'a': 2}), Counter()) == {
        'a': {'access': 2, 'tcc': 0, 'delta': 2}
    }


def test_multiset_diff_keys_only_on_right():
    assert multiset_diff(Counter(), Counter({'b': 5})) == {
        'b': {'access': 0, 'tcc': 5, 'delta': -5}
    }


def test_multiset_diff_negative_delta():
    assert multiset_diff(Counter({'k': 1}), Counter({'k': 4})) == {
        'k': {'access': 1, 'tcc': 4, 'delta': -3}
    }
