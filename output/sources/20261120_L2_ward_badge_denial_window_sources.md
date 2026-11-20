# Sources for Ward Badge Denial Window

## Inspired by
https://www.hunton.com/privacy-and-cybersecurity-law-blog/ocr-settlement-emphasizes-importance-audit-controls (OCR settlement stressing regular audit log review; the nightly job reviews audit records but never bounds its counts in time)

## Concepts tested
- Sliding-window counting of denied events per principal with explicit window boundaries
- Timezone-aware timestamp comparison
- Principal normalisation (trimming and case folding) before grouping
- Threshold comparisons on integer counts

## Trap
Events whose timestamp sits exactly on the window start must be excluded, and events recorded with a different UTC offset than another event of the same instant must compare as the same moment. A naive string comparison or an inclusive lower bound gives counts that are off by one on boundary values.

## Key concepts found for the topic
- Normalize heterogeneous log timestamps to a single timezone and ordering before correlating events, since clock skew and mixed formats create false sequences
- Baseline normal per-user access patterns (volume, hours, resources) so that deviations can be scored rather than relying on fixed global thresholds
- Sliding-window counting of failed or denied events per principal and per source, with explicit window boundaries and handling of events exactly on the boundary
- Distinguishing break-glass or emergency access from genuine intrusion, using documented justification fields and separate review queues
- Correlating events across sources (badge, EHR, VPN, directory) by a stable identifier, accounting for shared workstations and aliased usernames
- Preserving log integrity and chain of custody, so that analysis never modifies the source records and findings cite exact event IDs

## Searches
- hospital EHR break-glass access audit log review OCR settlement findings
- health system insider snooping VIP patient record access detection case study
- hospital badge access logs correlated with EHR audit trail intrusion investigation postmortem

## Pages found
- [Designing Break-Glass Access the Preserves Accountability](https://louis.uah.edu/cgi/viewcontent.cgi?article=1996&context=honors-capstones)
- [What Is Break Glass Access? Emergency Access Guide | OLOID](https://www.oloid.com/blog/break-glass-access)
- [Healthcare Insider Risk Management | HIPAA Compliance & Patient Data Protection | Insider Risk Index](https://insiderisk.io/industries/healthcare)
- [OCR Settlement Emphasizes Importance of Audit Controls](https://www.hunton.com/privacy-and-cybersecurity-law-blog/ocr-settlement-emphasizes-importance-audit-controls)
- [How to Document EHR Access Audit Log Reviews for High‑Profile Patients: A Step-by-Step Guide](https://www.accountablehq.com/post/how-to-document-ehr-access-audit-log-reviews-for-high-profile-patients-a-step-by-step-guide)
