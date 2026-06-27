"""access_harness.extract -- metadata + data extraction from Microsoft Access.

CRITICAL DRIVER FACT (verified on this machine, 2026-06-26):
  The Microsoft Access ODBC driver (ACEODBC.DLL) catalog methods are
  unreliable / unsupported and are FORBIDDEN in this harness:
    * cursor.columns()      -- raises UnicodeDecodeError on some installs
                               (33/79 tables observed elsewhere); on this
                               machine it happens to succeed, but it is
                               banned by policy because we cannot trust it.
    * cursor.primaryKeys()  -- raises IM001 "Driver does not support this".
    * cursor.foreignKeys()  -- raises IM001 "Driver does not support this".

  This module sources ALL metadata the WORKING way instead:
    * columns        : cursor.description of "SELECT * FROM [t] WHERE 1=0"
                       mapped through access_harness.typemap.map_description.
    * primary key    : cursor.statistics() PrimaryKey index, ordinal order.
    * unique indexes : cursor.statistics() unique indexes.
    * foreign keys   : ACE OLE DB OpenSchema(adSchemaForeignKeys) via pywin32.
    * rich indexes   : ACE OLE DB OpenSchema(adSchemaIndexes) via pywin32.
    * saved queries  : ACE OLE DB OpenSchema(adSchemaProcedures UNION
                       adSchemaViews) via pywin32.

  tests/test_forbidden_methods.py enforces -- by both a source scan and a
  monkeypatch trap -- that none of the forbidden methods are ever called.

SURROGATE-TOLERANT DECODING:
  Some text columns in the real data contain lone UTF-16 surrogates that the
  default pyodbc decoder cannot round-trip (raises UnicodeDecodeError on data
  reads).  connect_data() registers a custom WCHAR decoder
  (utf-16-le / surrogatepass) so read_rows() never crashes on such cells.
  This affects DATA reads only; the metadata functions probe empty rowsets
  (WHERE 1=0) and are unaffected.
"""
from typing import Iterator, Optional

import pyodbc

from access_harness.typemap import ColumnType, map_description

# ---------------------------------------------------------------------------
# ACE OLE DB OpenSchema constants (verified against ACE.OLEDB.16.0).
# ---------------------------------------------------------------------------
ADSCHEMA_TABLES = 20
ADSCHEMA_COLUMNS = 4
ADSCHEMA_INDEXES = 12
ADSCHEMA_FOREIGN_KEYS = 27
ADSCHEMA_PROCEDURES = 16
ADSCHEMA_VIEWS = 23


# ---------------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------------
def _odbc_conn_str(path: str) -> str:
    return (
        "DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={path};ReadOnly=1;"
    )


def connect_data(path: str) -> pyodbc.Connection:
    """Open a READ-ONLY pyodbc connection to an .accdb / .mdb file.

    Registers a surrogate-tolerant WCHAR decoder so that data rows containing
    lone UTF-16 surrogates do not raise UnicodeDecodeError on read.
    """
    conn = pyodbc.connect(_odbc_conn_str(path), readonly=True)
    # Decode wide text as utf-16-le with surrogatepass so lone surrogates in
    # the real data survive the round trip instead of crashing the reader.
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding="utf-16-le")
    conn.setdecoding(pyodbc.SQL_WMETADATA, encoding="utf-16-le")
    return conn


def connect_ace(path: str):
    """Open a READ-ONLY ACE OLE DB ADODB.Connection (pywin32).

    Returns the opened win32com ADODB.Connection.  Caller is responsible for
    calling .Close().  Imported lazily so the module imports without pywin32
    on non-Windows machines (the integration tests skip there).
    """
    import win32com.client  # lazy: only needed for the ACE path

    ace = win32com.client.Dispatch("ADODB.Connection")
    ace.Open(
        f"Provider=Microsoft.ACE.OLEDB.16.0;Data Source={path};Mode=Read;"
    )
    return ace


# ---------------------------------------------------------------------------
# ACE OpenSchema helper
# ---------------------------------------------------------------------------
def _open_schema_rows(ace_conn, schema_const: int) -> Iterator[dict]:
    """Yield each row of an ACE OpenSchema rowset as a {field_name: value} dict."""
    rs = ace_conn.OpenSchema(schema_const)
    try:
        field_names = [rs.Fields.Item(i).Name for i in range(rs.Fields.Count)]
        while not rs.EOF:
            yield {name: rs.Fields.Item(name).Value for name in field_names}
            rs.MoveNext()
    finally:
        rs.Close()


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def list_user_tables(ace_conn) -> list:
    """Return the user TABLE names (TABLE_TYPE == 'TABLE'), sorted.

    Excludes 'ACCESS TABLE', 'SYSTEM TABLE', and 'VIEW'.
    """
    names = [
        row["TABLE_NAME"]
        for row in _open_schema_rows(ace_conn, ADSCHEMA_TABLES)
        if row.get("TABLE_TYPE") == "TABLE"
    ]
    return sorted(names)


# ---------------------------------------------------------------------------
# Columns (cursor.description -- never cursor.columns())
# ---------------------------------------------------------------------------
def column_meta(conn, table: str) -> list:
    """Return [ColumnType] for a table via cursor.description of an empty probe.

    Uses "SELECT * FROM [table] WHERE 1=0" so no data is fetched; the column
    metadata comes entirely from cursor.description and is mapped through
    access_harness.typemap.map_description.
    """
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM [{table}] WHERE 1=0")
        return [map_description(d) for d in cur.description]
    finally:
        cur.close()


# ---------------------------------------------------------------------------
# Primary key + unique indexes (cursor.statistics() -- never primaryKeys())
# ---------------------------------------------------------------------------
# pyodbc statistics() rowset positions (DB API ordering):
#   3 non_unique, 5 index_name, 6 type, 7 ordinal_position, 8 column_name
_STAT_NON_UNIQUE = 3
_STAT_INDEX_NAME = 5
_STAT_TYPE = 6
_STAT_ORDINAL = 7
_STAT_COLUMN = 8
# SQL_TABLE_STAT marker rows have type == 0 and no column; real index rows have
# a column name and an ordinal.  Access names the declared PK index "PrimaryKey".
_PK_INDEX_NAME = "PrimaryKey"


def _statistics_rows(conn, table: str) -> list:
    cur = conn.cursor()
    try:
        return cur.statistics(table).fetchall()
    finally:
        cur.close()


def primary_key(conn, table: str) -> list:
    """Return the declared primary-key columns in ordinal order.

    Reads cursor.statistics(); the declared PK is the index named 'PrimaryKey'.
    Returns [] if the table has no declared primary key.
    """
    rows = _statistics_rows(conn, table)
    pk = [
        r
        for r in rows
        if r[_STAT_INDEX_NAME] == _PK_INDEX_NAME and r[_STAT_COLUMN] is not None
    ]
    pk.sort(key=lambda r: r[_STAT_ORDINAL])
    return [r[_STAT_COLUMN] for r in pk]


def unique_indexes(conn, table: str) -> list:
    """Return unique indexes as [{'name', 'columns', 'is_unique'}].

    Reads cursor.statistics(); a row is a unique index when non_unique == 0.
    Columns are ordered by ordinal_position within each index.  The declared
    PrimaryKey index is included (it is unique).
    """
    rows = _statistics_rows(conn, table)
    by_index: dict = {}
    for r in rows:
        name = r[_STAT_INDEX_NAME]
        col = r[_STAT_COLUMN]
        non_unique = r[_STAT_NON_UNIQUE]
        if col is None or name is None:
            continue  # SQL_TABLE_STAT marker row -- not an index column
        if non_unique != 0:
            continue  # non-unique index
        entry = by_index.setdefault(
            name, {"name": name, "_cols": [], "is_unique": True}
        )
        entry["_cols"].append((r[_STAT_ORDINAL], col))
    result = []
    for entry in by_index.values():
        cols = [c for _ord, c in sorted(entry["_cols"], key=lambda t: t[0])]
        result.append(
            {"name": entry["name"], "columns": cols, "is_unique": entry["is_unique"]}
        )
    result.sort(key=lambda e: e["name"])
    return result


# ---------------------------------------------------------------------------
# Foreign keys + rich indexes (ACE OpenSchema -- never foreignKeys())
# ---------------------------------------------------------------------------
def foreign_keys(ace_conn, table: str) -> list:
    """Return foreign keys whose CHILD (FK) table is `table`.

    Each entry: {'fk_name', 'fk_column', 'pk_table', 'pk_column', 'ordinal'}.
    Sourced from ACE OpenSchema(adSchemaForeignKeys).
    """
    result = []
    for row in _open_schema_rows(ace_conn, ADSCHEMA_FOREIGN_KEYS):
        if row.get("FK_TABLE_NAME") != table:
            continue
        result.append(
            {
                "fk_name": row.get("FK_NAME"),
                "fk_column": row.get("FK_COLUMN_NAME"),
                "pk_table": row.get("PK_TABLE_NAME"),
                "pk_column": row.get("PK_COLUMN_NAME"),
                "ordinal": row.get("ORDINAL"),
            }
        )
    result.sort(key=lambda e: (e["fk_name"] or "", e["ordinal"] or 0))
    return result


def indexes(ace_conn, table: str) -> list:
    """Return all indexes for a table via ACE OpenSchema(adSchemaIndexes).

    Each entry: {'name', 'columns', 'is_unique', 'is_primary_key'} with
    columns ordered by ORDINAL_POSITION.
    """
    by_index: dict = {}
    for row in _open_schema_rows(ace_conn, ADSCHEMA_INDEXES):
        if row.get("TABLE_NAME") != table:
            continue
        name = row.get("INDEX_NAME")
        entry = by_index.setdefault(
            name,
            {
                "name": name,
                "_cols": [],
                "is_unique": bool(row.get("UNIQUE")),
                "is_primary_key": bool(row.get("PRIMARY_KEY")),
            },
        )
        entry["_cols"].append(
            (row.get("ORDINAL_POSITION"), row.get("COLUMN_NAME"))
        )
    result = []
    for entry in by_index.values():
        cols = [c for _ord, c in sorted(entry["_cols"], key=lambda t: (t[0] or 0))]
        result.append(
            {
                "name": entry["name"],
                "columns": cols,
                "is_unique": entry["is_unique"],
                "is_primary_key": entry["is_primary_key"],
            }
        )
    result.sort(key=lambda e: e["name"] or "")
    return result


# ---------------------------------------------------------------------------
# Saved queries (ACE OpenSchema procedures UNION views)
# ---------------------------------------------------------------------------
def saved_queries(ace_conn) -> list:
    """Return Access saved queries as [{'name', 'type', 'sql_text'}].

    Saved queries surface in two ACE schema rowsets:
      * adSchemaProcedures -> action queries (name PROCEDURE_NAME,
        sql PROCEDURE_DEFINITION).  type == 'procedure'.
      * adSchemaViews      -> select queries (name TABLE_NAME,
        sql VIEW_DEFINITION).  type == 'view'.
    Their union is the full saved-query set.
    """
    result = []
    for row in _open_schema_rows(ace_conn, ADSCHEMA_PROCEDURES):
        result.append(
            {
                "name": row.get("PROCEDURE_NAME"),
                "type": "procedure",
                "sql_text": row.get("PROCEDURE_DEFINITION"),
            }
        )
    for row in _open_schema_rows(ace_conn, ADSCHEMA_VIEWS):
        result.append(
            {
                "name": row.get("TABLE_NAME"),
                "type": "view",
                "sql_text": row.get("VIEW_DEFINITION"),
            }
        )
    result.sort(key=lambda e: (e["type"], e["name"] or ""))
    return result


# ---------------------------------------------------------------------------
# Driver info + data reads
# ---------------------------------------------------------------------------
def driver_info(conn) -> tuple:
    """Return (driver_name, dbms_version) from the ODBC connection."""
    return (
        conn.getinfo(pyodbc.SQL_DRIVER_NAME),
        conn.getinfo(pyodbc.SQL_DBMS_VER),
    )


def read_rows(conn, table: str) -> Iterator[tuple]:
    """Yield data rows of a table as plain tuples (streamed)."""
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM [{table}]")
        while True:
            row = cur.fetchone()
            if row is None:
                break
            yield tuple(row)
    finally:
        cur.close()
