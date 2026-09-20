# Recoverable file operations

Rename and archive reserve destinations exclusively. Existing files are never overwritten. The source stays in place until the item path/status and operation journal commit together.

After an interruption, inspect GET /api/operations. POST /api/operations/recover finishes only a committed move whose source and destination still match the recorded digest. Uncommitted copies remain for operator review; they are never silently deleted. A destination collision returns HTTP 409, an invalid filename returns 422, and a missing source leaves the item unchanged.

Use the operation journal to inspect both paths before manually resolving an incomplete copy. Saved source data takes priority over automatic cleanup.
