"""access_harness.typemap -- pure logic, no DB connection required.

Maps pyodbc cursor.description 7-tuples to Postgres type metadata.
Does NOT call cursor.columns() / cursor.primaryKeys() / cursor.foreignKeys().
"""
import datetime
import decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnType:
    """Holds the type mapping result for one column."""
    access_type: str       # str(type_code) from cursor.description
    pg_type: str           # Postgres type string
    nullable: bool         # from null_ok (7th element of cursor.description)
    size: Optional[int]    # internal_size (4th element)
    precision: Optional[int]  # precision (5th element)
    round_trippable: bool  # True iff the mapping is lossless / recognized


# Map from Python type object -> Postgres type string.
# Only types that appear in pyodbc cursor.description are listed here.
_TYPE_MAP: dict = {
    int: 'integer',
    float: 'double precision',
    str: 'text',
    decimal.Decimal: 'numeric(19,4)',
    datetime.datetime: 'timestamp',
    bool: 'boolean',
    bytearray: 'bytea',
    bytes: 'bytea',
}


def map_description(desc_row: tuple) -> ColumnType:
    """Map one pyodbc cursor.description 7-tuple to a ColumnType.

    desc_row layout (per DB API 2.0 + pyodbc):
        0  name         str
        1  type_code    Python type object  (int, float, str, bool, ...)
        2  display_size int | None
        3  internal_size int | None
        4  precision    int | None
        5  scale        int | None
        6  null_ok      bool
    """
    _name, type_code, _display_size, internal_size, precision, _scale, null_ok = desc_row

    pg_type = _TYPE_MAP.get(type_code)
    if pg_type is not None:
        round_trippable = True
    else:
        pg_type = 'text'
        round_trippable = False

    return ColumnType(
        access_type=str(type_code),
        pg_type=pg_type,
        nullable=bool(null_ok),
        size=internal_size if internal_size else None,
        precision=precision if precision else None,
        round_trippable=round_trippable,
    )


def pg_ddl_type(ct: ColumnType) -> str:
    """Return the Postgres column type string for use in DDL.

    For most types this is just ct.pg_type.  For numeric the precision/scale
    are already baked into the string by map_description, so we pass through.
    """
    return ct.pg_type
