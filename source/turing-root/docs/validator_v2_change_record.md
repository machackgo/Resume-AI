# Validator and compatibility repair v2

The prospective catalog broadened non-degree education and historical evidence after the original pilot. First full-batch preflight exposed two factory defects, not fabricated teacher claims:

- Education entry titles accepted only `degree` fields, although an exact non-degree `credential` is legitimate education/training content. The v2 checker accepts exact credential values in Education while preserving event scope and exact text. It does not allow converting a certificate into a degree or an employment title. Four positive/negative regression controls exercise this boundary.
- The synthetic historical-record origin was absent from the frozen-context projection allowlist. It now maps explicitly to frozen `synthetic_fixture`, with the exact original origin retained in the inverse sidecar. It does not promote trust or run retrieval. Unknown aliases still reject.

The validator version is now `stage4c0-validator-v2`; the bridge report version is `stage4c0-frozen-context-bridge-v2`. Factory v1's manifest and complete source archive remain preserved at `work/factory-freeze-v1.json` and `work/factory-v1-archived-source.tar.gz`. Factory v2 supersedes that implementation snapshot. Teacher.v2, critic.v1, research principles, output schemas, rubrics, thresholds, scenario ground truth and saved raw outputs are unchanged. All selected targets must be audited again under validator v2; an earlier acceptance is not carried forward automatically.

Separate mapping failures involving extra requirement-irrelevant supporting facts remain failures. The oracle whitelist and UNKNOWN support-array gates are unchanged. Those outputs require bounded teacher revision or rejection, not weaker validation.

One remote test invocation expanded an unquoted shell wildcard and discovered zero tests. That log is retained and does not count as a successful test run. The replacement command names all test modules explicitly; local discovery with a quoted pattern executed the complete suite.
