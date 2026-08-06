import re


FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "detach",
    "pragma",
    "vacuum",
}


def validate_readonly_sql(sql: str) -> str:
    normalized = sql.strip()
    if not normalized:
        raise ValueError("SQL cannot be empty")

    if ";" in normalized.rstrip(";"):
        raise ValueError("Only one SQL statement is allowed")

    normalized = normalized.rstrip(";").strip()
    if not normalized.lower().startswith("select"):
        raise ValueError("Only SELECT statements are allowed")

    tokens = set(re.findall(r"[A-Za-z_]+", normalized.lower()))
    forbidden = sorted(tokens.intersection(FORBIDDEN_KEYWORDS))
    if forbidden:
        raise ValueError(f"Forbidden SQL keyword(s): {', '.join(forbidden)}")

    return normalized