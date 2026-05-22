"""SQL generator service for converting segment rules to SQL."""

from backend.config.features import SAFE_COLUMNS, get_feature
from backend.config.settings import get_settings
from backend.config.table_overrides import get_profiles_table
from backend.config.column_overrides import (
    get_profile_identity_household_column,
    get_profile_identity_individual_column,
)
from backend.models.segment import SegmentCondition, SegmentDefinition, SegmentGroup


class SqlGeneratorError(Exception):
    """Error in SQL generation."""

    pass


class SqlGenerator:
    """Generate SQL queries from segment definitions."""

    def __init__(self):
        self.settings = get_settings()  # for other settings if needed

    def _validate_column(self, column: str) -> str:
        """Validate column name against whitelist."""
        if column not in SAFE_COLUMNS:
            raise SqlGeneratorError(f"Invalid column: {column}")
        return column

    def _sanitize_string_value(self, value: str) -> str:
        """Sanitize string values for SQL (escape single quotes)."""
        return str(value).replace("'", "''")

    def _format_value(self, value: str | int | float | bool, feature_type: str) -> str:
        """Format a value for SQL based on feature type."""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if feature_type == "boolean":
            return "true" if str(value).lower() in ("true", "1", "yes") else "false"
        # String value
        return f"'{self._sanitize_string_value(value)}'"

    def _generate_bracket_case_expression(
        self, column: str, brackets: list[dict], bracket_style: str
    ) -> str:
        """Build a CASE WHEN expression from bracket definitions."""
        whens = []
        for b in brackets:
            label = self._sanitize_string_value(b["label"])
            has_min = "min" in b
            has_max = "max" in b

            if bracket_style == "inclusive":
                if has_min and has_max:
                    whens.append(
                        f"WHEN {column} BETWEEN {b['min']} AND {b['max']} THEN '{label}'"
                    )
                elif has_max:
                    whens.append(f"WHEN {column} < {b['max'] + 1} THEN '{label}'")
                elif has_min:
                    whens.append(f"WHEN {column} >= {b['min']} THEN '{label}'")
            else:  # exclusive_upper
                if has_min and has_max:
                    whens.append(
                        f"WHEN {column} >= {b['min']} AND {column} < {b['max']} THEN '{label}'"
                    )
                elif has_max:
                    whens.append(f"WHEN {column} < {b['max']} THEN '{label}'")
                elif has_min:
                    whens.append(f"WHEN {column} >= {b['min']} THEN '{label}'")

        return f"CASE {' '.join(whens)} ELSE NULL END"

    def _is_bracket_condition(self, condition: SegmentCondition, feature: dict) -> bool:
        """Check if a condition should use bracket-based SQL."""
        if not feature.get("brackets"):
            return False
        if condition.operator not in ("IN", "NOT"):
            return False
        bracket_labels = {b["label"] for b in feature["brackets"]}
        return all(str(v) in bracket_labels for v in condition.values)

    def _generate_condition_sql(self, condition: SegmentCondition) -> str:
        """Generate SQL for a single condition."""
        column = self._validate_column(condition.feature)
        feature = get_feature(condition.feature)

        if not feature:
            raise SqlGeneratorError(f"Unknown feature: {condition.feature}")

        feature_type = feature["type"]
        values = condition.values

        if not values:
            raise SqlGeneratorError(f"No values provided for condition on {column}")

        # Handle bracket-based IN/NOT conditions
        if self._is_bracket_condition(condition, feature):
            case_expr = self._generate_bracket_case_expression(
                column, feature["brackets"], feature.get("bracket_style", "inclusive")
            )
            sanitized_labels = [
                f"'{self._sanitize_string_value(str(v))}'" for v in values
            ]
            labels_sql = ", ".join(sanitized_labels)
            if condition.operator == "NOT":
                return f"{case_expr} NOT IN ({labels_sql})"
            return f"{case_expr} IN ({labels_sql})"

        # Handle different operators
        if condition.operator == "IS":
            formatted = self._format_value(values[0], feature_type)
            return f"{column} = {formatted}"

        elif condition.operator == "IN":
            formatted_values = [self._format_value(v, feature_type) for v in values]
            return f"{column} IN ({', '.join(formatted_values)})"

        elif condition.operator == "NOT":
            formatted_values = [self._format_value(v, feature_type) for v in values]
            return f"{column} NOT IN ({', '.join(formatted_values)})"

        elif condition.operator == "BETWEEN":
            if len(values) < 2:
                raise SqlGeneratorError("BETWEEN requires two values")
            min_val = self._format_value(values[0], feature_type)
            max_val = self._format_value(values[1], feature_type)
            return f"{column} BETWEEN {min_val} AND {max_val}"

        elif condition.operator == "GT":
            formatted = self._format_value(values[0], feature_type)
            return f"{column} > {formatted}"

        elif condition.operator == "LT":
            formatted = self._format_value(values[0], feature_type)
            return f"{column} < {formatted}"

        elif condition.operator == "GTE":
            formatted = self._format_value(values[0], feature_type)
            return f"{column} >= {formatted}"

        elif condition.operator == "LTE":
            formatted = self._format_value(values[0], feature_type)
            return f"{column} <= {formatted}"

        else:
            raise SqlGeneratorError(f"Unknown operator: {condition.operator}")

    def _is_valid_condition(self, condition: SegmentCondition) -> bool:
        """Check if a condition is valid (has feature and values)."""
        return bool(condition.feature and condition.values)

    def _generate_group_sql(self, group: SegmentGroup) -> str:
        """Generate SQL for a group of conditions."""
        if not group.conditions:
            return "1=1"  # Empty group matches all

        condition_sqls = []
        for condition in group.conditions:
            # Skip incomplete conditions
            if not self._is_valid_condition(condition):
                continue

            sql = self._generate_condition_sql(condition)

            # Handle nullable columns
            feature = get_feature(condition.feature)
            if feature and feature.get("nullable"):
                sql = f"({condition.feature} IS NOT NULL AND {sql})"

            condition_sqls.append(sql)

        # If all conditions were skipped, return match all
        if not condition_sqls:
            return "1=1"

        joiner = f" {group.logic} "
        return f"({joiner.join(condition_sqls)})"

    def generate_where_clause(self, segment: SegmentDefinition) -> str:
        """Generate the WHERE clause from a segment definition."""
        if not segment.groups:
            return "1=1"  # No conditions, match all

        group_sqls = [self._generate_group_sql(group) for group in segment.groups]
        joiner = f" {segment.group_logic} "
        return joiner.join(group_sqls)

    def generate_count_query(self, segment: SegmentDefinition) -> str:
        """Generate a COUNT query for segment preview."""
        where_clause = self.generate_where_clause(segment)

        ind_col = get_profile_identity_individual_column()
        hh_col = get_profile_identity_household_column()
        return f"""
SELECT
    COUNT(DISTINCT {ind_col}) as individual_count,
    COUNT(DISTINCT {hh_col}) as household_count
FROM {get_profiles_table()}
WHERE {where_clause}
        """.strip()

    def generate_select_query(self, segment: SegmentDefinition) -> str:
        """Generate a SELECT query to get segment members."""
        where_clause = self.generate_where_clause(segment)
        ind_col = get_profile_identity_individual_column()
        hh_col = get_profile_identity_household_column()
        return f"""
SELECT {ind_col}, {hh_col}
FROM {get_profiles_table()}
WHERE {where_clause}
        """.strip()


# Singleton instance
_generator: SqlGenerator | None = None


def get_sql_generator() -> SqlGenerator:
    """Get the singleton SQL generator."""
    global _generator
    if _generator is None:
        _generator = SqlGenerator()
    return _generator
