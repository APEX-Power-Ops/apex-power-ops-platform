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
# A numeric/Decimal column (pg_type 'numeric(19,4)').
DT = ColumnType('decimal', 'numeric(19,4)', True, None, 19, True)
# A timestamp/datetime column.
TS = ColumnType('datetime', 'timestamp', True, None, None, True)
# A bytea/bytes column.
BY = ColumnType('bytes', 'bytea', True, None, None, True)

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


def test_canonical_row_null_token_is_fixed():
    # NULL is the bare typed token "N" (injective encoding); distinct from any
    # "V"-tagged value token.
    assert canonical_row((None,), [ST]) == 'N'


def test_canonical_row_separator_joins_fixed_order():
    # Columns joined in given order with the 0x01 separator; each field is a
    # typed, length-prefixed token ("V" + len + ":" + enc).
    assert canonical_row((1, 1.5), T) == 'V1:1\x01V3:1.5'


def test_canonical_row_real_type_is_float_formatted():
    # 'real' pg_type also uses .17g formatting.
    assert canonical_row((0.1 + 0.2,), [RT]) == canonical_row((0.30000000000000004,), [RT])


def test_canonical_row_non_float_uses_str():
    # Integer column: plain str() inside the token, not .17g.
    assert canonical_row((42,), [IT]) == 'V2:42'


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


# --- Injectivity: no separator / sentinel collisions (IMPORTANT #1) ---------


def test_no_collision_when_cell_contains_separator():
    # ('a\x01b','c') and ('a','b\x01c') must NOT canonicalize identically:
    # data content can never shift a field boundary.
    assert canonical_row(('a\x01b', 'c'), [ST, ST]) != canonical_row(
        ('a', 'b\x01c'), [ST, ST]
    )


def test_text_cell_equal_to_sentinel_is_not_null():
    # A text cell whose value happens to equal the old NULL sentinel string
    # must NOT collide with a real SQL None.
    assert canonical_row(('\x00NULL',), [ST]) != canonical_row((None,), [ST])


def test_no_collision_empty_string_vs_null_still_holds():
    # Regression: None and '' stay distinct under the new encoding.
    assert canonical_row((None,), [ST]) != canonical_row(('',), [ST])


def test_no_collision_length_prefix_boundary():
    # Classic length-prefix attack: ('1', '2:ab') vs ('1:2', ':ab')-style
    # shifts must not collide.  Distinct field splits -> distinct canon.
    assert canonical_row(('1', '23'), [ST, ST]) != canonical_row(
        ('12', '3'), [ST, ST]
    )


# --- Byte-stable canonicalization for typed values (IMPORTANT #2) -----------


def test_decimal_scale_normalized_equal():
    import decimal
    # Decimal('1.50') and Decimal('1.5') are numerically equal -> same canon.
    assert canonical_row((decimal.Decimal('1.50'),), [DT]) == canonical_row(
        (decimal.Decimal('1.5'),), [DT]
    )


def test_decimal_distinct_values_differ():
    import decimal
    assert canonical_row((decimal.Decimal('1.5'),), [DT]) != canonical_row(
        (decimal.Decimal('1.6'),), [DT]
    )


def test_datetime_isoformat_canonical():
    import datetime
    a = datetime.datetime(2020, 1, 1, 0, 0, 0)
    b = datetime.datetime(2020, 1, 1, 0, 0, 0)
    assert canonical_row((a,), [TS]) == canonical_row((b,), [TS])


def test_datetime_uses_isoformat_not_str():
    import datetime
    a = datetime.datetime(2020, 1, 2, 3, 4, 5)
    canon = canonical_row((a,), [TS])
    # isoformat embeds the 'T' separator; str() uses a space.  Assert isoformat.
    assert '2020-01-02T03:04:05' in canon


def test_date_isoformat_canonical():
    import datetime
    d = datetime.date(2020, 1, 2)
    canon = canonical_row((d,), [TS])
    assert '2020-01-02' in canon


def test_bytes_canonical_hex():
    canon = canonical_row((b'\x00\x01',), [BY])
    # Deterministic + hex-encoded: bytes 00 01 -> '0001' appears in the canon.
    assert canon is not None
    assert '0001' in canon


def test_bytearray_canonical_hex_equals_bytes():
    assert canonical_row((bytearray(b'\xde\xad'),), [BY]) == canonical_row(
        (b'\xde\xad',), [BY]
    )


# --- Arity guard (MINOR #1) -------------------------------------------------


def test_canonical_row_arity_mismatch_raises():
    import pytest
    with pytest.raises(ValueError):
        canonical_row((1, 2), [IT])  # 2 values, 1 col_type


def test_canonical_row_arity_mismatch_extra_coltype_raises():
    import pytest
    with pytest.raises(ValueError):
        canonical_row((1,), [IT, FT])  # 1 value, 2 col_types
