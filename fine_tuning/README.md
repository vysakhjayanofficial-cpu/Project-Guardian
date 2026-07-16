### AI led Medical Review Assistant

Assist medical reviewers to assess seriousness, suggest MedDRA codes, evaluate labelling status, and support causality assessments.

{
    "seriousness_assessment",
    "seriousness_rationale",
    "meddra_pt",
    "meddra_soc",
    "labeling_status",
    "causality_assessment",
    "causality_rationale",
    "review_summary"
}

Public AE datasets

Useful starting points:

FAERS
VAERS
SIDER
MIMIC (with approvals)

These can provide:

Drug names
Adverse events
Outcomes

https://github.com/Mahdi-CV/amd-gpu-workshops/blob/main/notebooks/build_agents.ipynb

Test case format::

{
  "input": {
    "narrative": "Patient developed anaphylaxis 15 minutes after receiving Drug X and required hospitalization."
  },
  "output": {
    "seriousness": "Serious",
    "seriousness_reason": "Hospitalization",
    "meddra_pt": "Anaphylactic reaction",
    "causality": "Probable",
    "expectedness": "Unexpected"
  }
}