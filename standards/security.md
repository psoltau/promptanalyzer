# Company Security Standards

Reference: [OWASP Top 10 2025](https://owasp.org/Top10/2025/)

## Checklist

- No credentials, tokens, or API keys in source code
- All input validated at system boundaries with allow-list approach
- All database queries use parameterized statements — no string concatenation
- CORS origins are explicit lists — no wildcards in production
