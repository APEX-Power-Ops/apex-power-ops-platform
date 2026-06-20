import os

import psycopg
import pytest

from learning_resolver.db import dsn as _dsn


@pytest.fixture(scope="session")
def dsn() -> str:
    return _dsn()


def _scalar(d, sql):
    with psycopg.connect(d, autocommit=True) as c:
        row = c.execute(sql).fetchone()
        return row[0] if row else None


@pytest.fixture(scope="session")
def section_with_curated(dsn) -> str:
    """A NETA section whose apparatus_type carries the most curated resources."""
    return _scalar(dsn, """
        select np.section_number
        from neta_procedures np
        join apparatus_type_resources atr
          on atr.apparatus_type_id = np.apparatus_type_id and atr.is_active
        where np.section_number is not null
        group by np.section_number order by count(*) desc limit 1
    """)


@pytest.fixture(scope="session")
def section_study_only(dsn) -> str:
    """A study_content section with NO curated link via a procedure (section-join only)."""
    return _scalar(dsn, """
        select sc.neta_section_primary
        from study_content sc
        where sc.neta_section_primary is not null and sc.is_active and sc.status = 'published'
          and not exists (
            select 1 from neta_procedures np
            join apparatus_type_resources atr on atr.apparatus_type_id = np.apparatus_type_id
            where np.section_number = sc.neta_section_primary)
        group by sc.neta_section_primary limit 1
    """)
