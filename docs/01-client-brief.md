# 01 · Client brief (FICTIONAL)

> Pine Harbor Mutual is a made-up company. Every person, applicant, broker and document in this repo is synthetic. Independent learning project; not affiliated with any insurer or university program.

**Client:** Pine Harbor Mutual, a (fictional) regional commercial property insurer in Maine.
**Sponsor:** VP of Commercial Underwriting.
**Line of business:** small commercial property (retail, restaurants, light manufacturing, warehouses).

## What they told us
Each new submission arrives as three PDFs:
1. **Application** (filled in by the broker): applicant, address, broker, building facts (year built, square footage, construction, sprinklers), prior claims disclosed, requested limit.
2. **Loss run** (from the prior carrier): every claim in the last five years.
3. **Inspection report** (field inspector): what the building really looks like.

Underwriters re-type these into their head, then cross-check them against the policy system (internal records). It takes most of each file. Two things slip through:
- **Mismatches inside a file:** the application says 8,000 sq ft and sprinklered, the inspection says 11,500 sq ft and no sprinklers; the application says "0 prior claims", the loss run lists three.
- **Links across files:** the same broker or mailing address keeps showing up behind applicants with bad loss history. Nobody sees it because each file is read alone.

## The ask
"A prototype that pre-checks each file, explains every flag with a quote from the document, and sends only the riskiest files to a senior underwriter. It must never decline anyone by itself."

## Constraints from the sponsor
- A human underwriter makes every decision. The tool can only say **standard review** or **refer to senior underwriter**.
- Every flag must quote the document it came from.
- Documents may contain text written to manipulate an automated system. That text must never change a route.
- Runs on their own infrastructure (containerised), keys from environment only.
