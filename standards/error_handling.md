# Error Handling Standards

## Checklist

- All exceptions are either handled or propagated — no silent swallows
- Error responses use standard envelope with `code`, `message`, `traceId`
- `code` is `UPPER_SNAKE_CASE` string, not an HTTP status number
- Unexpected errors logged at ERROR with full stack trace
