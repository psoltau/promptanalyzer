# Code Quality Standards

## Checklist

- Every function ≤ 20 lines; split if longer
- Every function ≤ 3 parameters; use record/object for more
- No magic literals — all constants named and typed
- No unused imports, variables, or dead code
- No deeply nested conditionals (> 2 levels → extract or return early)
- Code reviewed by at least one other senior agent
- No inner static classes
