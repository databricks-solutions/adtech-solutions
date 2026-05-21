"""Unit tests for SqlGenerator: column validation, escaping, SQL shape."""

import pytest

from backend.models.segment import SegmentCondition, SegmentDefinition, SegmentGroup
from backend.services.sql_generator import SqlGenerator, SqlGeneratorError


@pytest.fixture
def sql_generator():
    """Fresh SqlGenerator instance (uses real SAFE_COLUMNS and get_feature from config)."""
    return SqlGenerator()


# --- Column validation ---


def test_validate_column_accepts_safe_columns(sql_generator):
    """Valid column names from SAFE_COLUMNS are accepted."""
    assert sql_generator._validate_column("state") == "state"
    assert sql_generator._validate_column("age") == "age"
    assert sql_generator._validate_column("is_dog_owner") == "is_dog_owner"
    assert sql_generator._validate_column("gender") == "gender"


def test_validate_column_rejects_invalid_columns(sql_generator):
    """Invalid column names raise SqlGeneratorError."""
    with pytest.raises(SqlGeneratorError, match="Invalid column: evil_column"):
        sql_generator._validate_column("evil_column")
    with pytest.raises(SqlGeneratorError, match="Invalid column: state; DROP TABLE"):
        sql_generator._validate_column("state; DROP TABLE")
    with pytest.raises(SqlGeneratorError, match="Invalid column: 1=1"):
        sql_generator._validate_column("1=1")


# --- String sanitization (SQL injection) ---


def test_sanitize_string_escapes_single_quotes(sql_generator):
    """Single quotes in values are doubled for SQL safety."""
    assert sql_generator._sanitize_string_value("O'Brien") == "O''Brien"
    # Every ' becomes ''; so ') OR ('1'='1 -> '') OR (''1''=''1
    assert sql_generator._sanitize_string_value("') OR ('1'='1") == "'') OR (''1''=''1"


def test_sanitize_string_passes_through_safe_strings(sql_generator):
    """Strings without quotes are unchanged."""
    assert sql_generator._sanitize_string_value("CA") == "CA"
    assert sql_generator._sanitize_string_value("Male") == "Male"


# --- Value formatting ---


def test_format_value_boolean(sql_generator):
    """Booleans become true/false literals."""
    assert sql_generator._format_value(True, "boolean") == "true"
    assert sql_generator._format_value(False, "boolean") == "false"


def test_format_value_numeric(sql_generator):
    """Numbers are passed through as literals."""
    assert sql_generator._format_value(42, "numeric") == "42"
    assert sql_generator._format_value(18.5, "numeric") == "18.5"


def test_format_value_string_quoted_and_escaped(sql_generator):
    """String values are single-quoted and escaped."""
    assert sql_generator._format_value("CA", "categorical") == "'CA'"
    assert sql_generator._format_value("O'Brien", "categorical") == "'O''Brien'"


# --- Condition SQL generation ---


def _condition(feature: str, operator: str, values: list) -> SegmentCondition:
    return SegmentCondition(id="c1", feature=feature, operator=operator, values=values)


def test_generate_condition_sql_is_operator(sql_generator):
    """IS operator produces column = value."""
    cond = _condition("state", "IS", ["CA"])
    assert sql_generator._generate_condition_sql(cond) == "state = 'CA'"


def test_generate_condition_sql_in_operator(sql_generator):
    """IN operator produces column IN (values)."""
    cond = _condition("state", "IN", ["CA", "TX"])
    sql = sql_generator._generate_condition_sql(cond)
    assert "state IN (" in sql
    assert "'CA'" in sql
    assert "'TX'" in sql


def test_generate_condition_sql_not_operator(sql_generator):
    """NOT operator produces column NOT IN (values)."""
    cond = _condition("gender", "NOT", ["Unknown"])
    sql = sql_generator._generate_condition_sql(cond)
    assert "gender NOT IN (" in sql
    assert "'Unknown'" in sql


def test_generate_condition_sql_between(sql_generator):
    """BETWEEN operator produces column BETWEEN min AND max."""
    cond = _condition("age", "BETWEEN", [25, 54])
    assert sql_generator._generate_condition_sql(cond) == "age BETWEEN 25 AND 54"


def test_generate_condition_sql_between_requires_two_values(sql_generator):
    """BETWEEN with one value raises."""
    cond = _condition("age", "BETWEEN", [25])
    with pytest.raises(SqlGeneratorError, match="BETWEEN requires two values"):
        sql_generator._generate_condition_sql(cond)


def test_generate_condition_sql_empty_values_raises(sql_generator):
    """Condition with no values raises."""
    cond = _condition("state", "IS", [])
    with pytest.raises(SqlGeneratorError, match="No values provided"):
        sql_generator._generate_condition_sql(cond)


def test_generate_condition_sql_boolean_is(sql_generator):
    """Boolean feature with IS true/false."""
    cond = _condition("is_dog_owner", "IS", [True])
    assert sql_generator._generate_condition_sql(cond) == "is_dog_owner = true"


# --- Full query shape ---


def test_generate_where_clause_empty_groups(sql_generator):
    """Empty groups produce 1=1."""
    segment = SegmentDefinition(name="", description="", groups=[], groupLogic="AND")
    assert sql_generator.generate_where_clause(segment) == "1=1"


def test_generate_where_clause_single_condition(sql_generator):
    """Single condition produces (col = val)."""
    segment = SegmentDefinition(
        name="",
        description="",
        groups=[
            SegmentGroup(
                id="g1",
                logic="AND",
                conditions=[_condition("state", "IS", ["CA"])],
            )
        ],
        groupLogic="AND",
    )
    where = sql_generator.generate_where_clause(segment)
    assert "state = 'CA'" in where
    assert "1=1" not in where


def test_generate_count_query_contains_expected_parts(sql_generator):
    """Count query includes FROM, WHERE, COUNT DISTINCT, and profile table."""
    segment = SegmentDefinition(
        name="",
        description="",
        groups=[
            SegmentGroup(
                id="g1",
                logic="AND",
                conditions=[_condition("state", "IS", ["CA"])],
            )
        ],
        groupLogic="AND",
    )
    sql = sql_generator.generate_count_query(segment)
    assert "COUNT(DISTINCT megacorp_indid)" in sql
    assert "COUNT(DISTINCT megacorp_hhid)" in sql
    assert "FROM media_advertising.profiles.megacorp_audience_census_profile" in sql
    assert "WHERE" in sql
    assert "state = 'CA'" in sql
