# Smoke v1 review, before full benchmark

Run grounded-v1-smoke-2325384-1, step 2325384.9. Strict schema valid. 531 tokens in 57.184 seconds. Skills r/power_bi only. Unknown credential remained UNKNOWN. Invented error reduction rejected. One supported R/CSV bullet, no unsupported additions.

Compound S2 (created AND deployed) was labeled UNSUPPORTED although creation is supported; expected PARTIALLY_SUPPORTED. The v1 rule "or evidence explicitly denies it" conflicts with compound decomposition and appears to encourage treating a denied component as denial of the entire compound. v2 clarifies generic atomic precedence: mixed supported/denied parts produce PARTIALLY_SUPPORTED, while a denied indivisible claim remains UNSUPPORTED. No benchmark facts/examples added.

Standalone production_deployment was also UNSUPPORTED versus smoke gold PARTIALLY_SUPPORTED. That gold label is debatable because local creation need not imply any deployment. Do not change smoke gold or add a rule forcing this label; report this rubric issue. The eight-case benchmark and gold remain untouched. Use the second smoke to test the compound correction, then freeze before full evaluation.
