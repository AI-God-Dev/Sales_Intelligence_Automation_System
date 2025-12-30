# ADR-002: Date Serialization in JSON

## Status
Accepted

## Context
The account scoring function was failing intermittently with:
```
TypeError: Object of type date is not JSON serializable
```

This occurred when `account_data` from BigQuery queries contained Python `date` and `datetime` objects that couldn't be serialized to JSON for the LLM prompt.

## Decision
Implement a custom JSON serializer function that converts `date` and `datetime` objects to ISO format strings.

### Implementation
```python
def _json_serializer(obj: Any) -> str:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)

# Usage
json.dumps(account_data, default=_json_serializer, ensure_ascii=False)
```

## Consequences

### Positive
- ✅ All date/datetime objects properly serialized
- ✅ ISO format is standard and LLM-friendly
- ✅ Backward compatible with existing code
- ✅ Handles edge cases gracefully

### Negative
- ❌ Slight performance overhead (minimal)
- ❌ Requires explicit serializer in JSON dumps calls

## Alternatives Considered

### Convert dates before passing to JSON
- **Pros**: No serializer needed
- **Cons**: Requires manual conversion everywhere, error-prone
- **Decision**: Rejected due to maintenance burden

### Use string representation everywhere
- **Pros**: Simple
- **Cons**: Loses type information, harder to parse back
- **Decision**: Rejected in favor of ISO format

## Implementation Notes
- Added to `ai/scoring.py` in `_build_prompt()` method
- Includes error handling with fallback to string representation
- ISO format ensures consistent date representation

