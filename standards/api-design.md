# REST API Design Standards

## Checklist

- URL starts with `/api/v{n}/` prefix
- All list endpoints have pagination with `MAX_PAGE_SIZE` cap
- Sort fields validated against a whitelist constant (`ALLOWED_SORT_FIELDS`)
- Resource IDs are UUIDs (not auto-increment integers)
- Error responses use standard envelope `{ error: { code, message, traceId } }`
- Created resources return 201 with `Location` header
