\# Phase 3 — Entity Resolution



\## Objective



Resolve records from Core, CRM, KYC and Wealth into likely common

customer identities using deterministic and fuzzy matching.



\## Pipeline



Silver

→ Candidate Blocking

→ Deterministic Matching

→ Fuzzy Matching

→ Explainable Scoring

→ MATCH / REVIEW / NO MATCH



\## Candidate Blocking



Blocking strategies:



\- DOB + postal code

\- Surname + DOB

\- Normalized email

\- Phone suffix



DEV results:



\- Silver records: 58,370

\- Candidate pairs: 679,839

\- True entity pairs: 55,441

\- Blocking recall: 99.4769%

\- Missed true pairs: 290



\## Deterministic Matching



Rules:



\- LEI exact

\- Tax ID exact

\- Phone + DOB exact

\- Email + DOB exact



Deterministic matches on DEV:



34,588



\## Fuzzy Matching



Field-level scores:



\- name\_score

\- address\_score

\- phone\_score

\- email\_score

\- dob\_score



RapidFuzz version:



3.14.6



\## Explainable Scoring



Initial weights:



\- Name: 30%

\- Address: 20%

\- Phone: 20%

\- Email: 15%

\- DOB: 15%



Missing fields are excluded from the weighted denominator.



Minimum comparable fields:



2



\## Final Decision Policy



After DEV threshold evaluation:



\- MATCH: score >= 85

\- REVIEW: 70 <= score < 85

\- NO MATCH: score < 70



\## Final DEV Results



Candidate pairs:



679,839



Deterministic matches:



34,588



Fuzzy MATCH:



19,439



REVIEW:



1,159



NO MATCH:



624,653



True positives:



54,023



False positives:



4



False negatives:



1,418



Precision:



99.9926%



Recall:



97.4423%



F1:



98.7010%



\## Threshold Tuning



The original MATCH threshold of 90 was tested against lower thresholds.



Final comparison:



| Threshold | Precision | Recall | F1 | FP | FN |

|-----------|-----------|--------|----|----|----|

| 90 | 99.9925% | 95.6657% | 97.7812% | 4 | 2,403 |

| 89 | 99.9925% | 95.9146% | 97.9111% | 4 | 2,265 |

| 88 | 99.9925% | 96.1509% | 98.0341% | 4 | 2,134 |

| 87 | 99.9925% | 96.5314% | 98.2315% | 4 | 1,923 |

| 86 | 99.9926% | 97.0058% | 98.4766% | 4 | 1,660 |

| 85 | 99.9926% | 97.4423% | 98.7010% | 4 | 1,418 |



Threshold 85 was selected because it produced the highest F1 and recall

among the tested configurations while maintaining extremely high

precision and the same false-positive count.



\## Explainability



Each fuzzy match result records:



\- source system

\- source ID

\- blocking keys

\- field-level scores

\- aggregate match score

\- matching rule

\- decision

\- reason



\## Scope Decision



No additional blocking strategy was added after evaluating

surname + postal code.



No ML or LLM matching was introduced.



Local processing is intentionally kept as a logic-validation stage.

The proven matching logic will later be ported to Azure Databricks /

PySpark.



\## Phase 3 Status



COMPLETE

