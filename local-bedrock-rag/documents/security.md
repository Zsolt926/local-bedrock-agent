# Security engineering notes

A retrieval-augmented application should enforce authorization before returning
documents. Metadata filters are useful for narrowing results, but metadata supplied
by a client must not be treated as an authorization decision.

Tool functions should expose only explicitly approved operations. Validate tool
arguments, constrain document scopes, and avoid logging secrets or sensitive content.
