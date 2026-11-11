# 02 · Discovery notes (SIMULATED interviews)

> These are role-played interviews written to practise a forward-deployed discovery loop. They are not real people or quotes.

## Interview 1 · Senior underwriter (8 years)
- "I spend 20–30 minutes per file just lining up the three documents."
- "The killers are undisclosed losses and a building that is bigger than the app says. Bigger building, same premium."
- "If a tool flags something, show me the sentence. I won't trust a score."
- Pain: re-reading; no memory across files.

## Interview 2 · Underwriting manager
- "I want my seniors on the hard 20%, not on clean files."
- "Last year we found a broker who kept placing the same family of businesses at one address. Each file looked fine alone."
- Success for her: risky files reach a senior; clean files don't pile up there.
- Pain: no cross-file view of brokers and addresses.

## Interview 3 · Compliance
- "Nothing gets declined by a machine. Adverse action needs a human and a reason."
- "Log who overrode what, and why."
- Points to the NAIC Model Bulletin on the Use of AI Systems by Insurers (Dec 2023): governance, documentation, human oversight.
- Pain: black-box tools she can't audit.

## What we heard (synthesis)
| Theme | Evidence | Implication for the build |
|---|---|---|
| In-file mismatches | interviews 1, 2 | structured extraction + field validators against internal records |
| Cross-file links (broker / address rings) | interview 2 | an entity graph; multi-hop questions a plain vector search misses |
| Trust needs quotes | interview 1 | every flag carries a verbatim quote |
| Human decides, logged | interview 3 | two routes only; review queue with approve / override + reason |
| Manipulated documents | brief | injected instructions must not change a route; tested |
