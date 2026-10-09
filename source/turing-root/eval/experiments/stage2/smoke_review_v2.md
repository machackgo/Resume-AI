# Smoke v2 review

Run grounded-v2-smoke-2325384-1, step 2325384.11. Strict JSON and schema passed, no invented metric, one grounded R/CSV bullet; unknown credential excluded from skills. 531 tokens, 57.331 seconds. Compound S2 still UNSUPPORTED (expected PARTIALLY_SUPPORTED); raw system text and rendered prompt verified to include the v2 revision, so this is a model instruction-following failure, not a stale prompt/load error. Both smoke metrics independently reproduced. No gold edits.

v3 adds a generic symbolic atomic-label decision table and a final UNSUPPORTED-label audit. A AND B with supported A and denied B is partial, whereas an indivisible denied B is unsupported. The same final audit applies to arbitrary actions/qualifiers, without smoke facts, test-case IDs, or expected answers. This is the final planned smoke-based revision; report any remaining taxonomy limitation honestly. Standalone deployment gold ambiguity remains documented rather than forced.
