# Labeling policy — skill tag audit

**Goal.** Check whether each model tag is a *required* skill for the job, using only the supplied approved skill list and the text of each fictional job description.

1. **Required skills.** Count skills stated in an explicit requirement, such as “Required,” “must be comfortable with,” “need someone who knows,” or “will use ... every day.” The required-skills list is the reference (“gold”) set for each JD.
2. **Optional skills.** Do not count skills described as “bonus,” “nice to have,” or “a plus, not a must” as requirements. If the model predicts an optional skill as a required tag, label it `WRONG_OPTIONAL`. For example, `JD034` predicts SEO although SEO is only nice to have.
3. **Aliases / spelling.** Normalize only unambiguous equivalents: Excel → Microsoft Excel; JS → JavaScript; Node → Node.js; Postgres → PostgreSQL; ML → Machine Learning; Financial Modeling → Financial Modelling; and, in this dataset's context, Social Media → Social Media Marketing. Compare normalized skills with the approved vocabulary. Do **not** normalize generic `API` to specific `REST APIs` (see `JD023`).
4. **Unapproved / unsupported predictions.** Mark a predicted tag `WRONG_OOV` if it is not in the approved skill vocabulary even after alias normalization (e.g., `JD001` Teamwork). Mark `WRONG_UNSUPPORTED` if it is an approved skill but not an explicitly required or optional skill for that job (e.g., `JD007` Kubernetes).
5. **Missing required skills.** A skill in the required set that no normalized model prediction covers is a false negative (`FN`). For example, `JD002` misses React. Count each unique required skill once per JD.
6. **Generic statements and inference.** Do not infer required skills from the job title, general duties, or the repeated “Good communication matters in this team” sentence. This is a deliberate *strict required-skill* policy; a different policy that includes soft skills would require recalculating results.

**Decision labels.** `CORRECT` = a model prediction matches a required skill; `WRONG_OPTIONAL` = predicted optional skill; `WRONG_OOV` = tag outside approved vocabulary; `WRONG_UNSUPPORTED` = approved skill with no requirement evidence. `missing_skills` lists required skills absent from predictions.

**Metrics.** TP = count of `CORRECT` model tags; FP = count of all `WRONG_*` predicted tags; FN = count of required skills not predicted. Precision = TP/(TP+FP), recall = TP/(TP+FN), miss rate = FN/(TP+FN). Here: TP 151, FP 49, FN 26; precision 75.50%, recall 85.31%, miss rate 14.69%.

**Review and limitations.** All 50 JD-level outputs were checked against the supplied descriptions in a guided review. This assessment uses strict requirement wording and a small explicit alias map, and does not measure the model on other descriptions. ChatGPT assisted with the initial rule-based labeling, code, calculations, spreadsheet and writing. The row-level judgments and source CSVs are provided for independent verification.
