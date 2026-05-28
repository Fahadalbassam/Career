# Representative Recommendation Examples (ML-4)

Generated from the test split using **`fair_gradient_boosting`** (best fair / leakage-safe model). Top opportunities are ordered by **rubric `target_score`** (ground-truth label for training). Predicted scores are the fair model's hold-out estimates.

> **Note:** Rubric-assisted models are not shown here — they exhibit near-perfect metrics due to target leakage and are for sanity-check only.

## Example 1: Cybersecurity / SOC (Dammam / Khobar)

- **Profile ID:** `eastern-province-cys`
- **User message:** Cybersecurity student in Dammam open to Khobar and Dhahran SOC roles.

**Parsed profile**

| Field | Value |
|---|---|
| major | CYS |
| city | Dammam |
| skills | linux |
| interest | — |
| program_type | COOP |
| work_mode | On-site |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Schneider Electric | Co-op Intern (Engineering) - Al Khobar (Jan–Aug 2026) | Network Engineering | 82.5 | 65.1 | 17.4 |
| 2 | NHC | COOP Trainee | Cybersecurity | 82.0 | 69.1 | 12.9 |
| 3 | Bank Albilad | Cooperative Training Program | Cybersecurity | 82.0 | 73.8 | 8.2 |
| 4 | Saudi Food & Drug Authority (SFDA) | COOP training (First semester 2025-2026 intake) | Cybersecurity | 82.0 | 69.1 | 12.9 |
| 5 | BSF (Banque Saudi Fransi) | COOP / Internship | Cybersecurity | 77.0 | 69.1 | 7.9 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (linux) and location preference (Dammam), surfacing clusters such as Network Engineering, Cybersecurity.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were far to rubric target scores (mean absolute error ≈ 11.9 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 2: Software engineering / backend

- **Profile ID:** `cs-iau-backend`
- **User message:** CS student at IAU with Python and SQL seeking backend developer internship in Riyadh or Dammam.

**Parsed profile**

| Field | Value |
|---|---|
| major | CS |
| city | Riyadh |
| skills | python; sql |
| interest | — |
| program_type | Internship |
| work_mode | Hybrid |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Tabby | Intern Data Engineer | Data Engineering | 91.5 | 81.4 | 10.1 |
| 2 | Lean Technologies | Software Engineering Intern – KSA | Software Engineering | 91.5 | 79.8 | 11.7 |
| 3 | Bosch Middle East | Software Development Intern (AI/Cloud) | Data Science | 88.5 | 83.1 | 5.4 |
| 4 | Tabby | Intern Backend (GO) Engineer | Software Engineering | 88.5 | 78.4 | 10.1 |
| 5 | Laverne Group | مجموعة لافيرن | Data Analyst / Data Engineer Intern (IT Department) | Data Analytics | 88.5 | 79.0 | 9.5 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (python; sql) and location preference (Riyadh), surfacing clusters such as Data Engineering, Software Engineering, Data Science.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were far to rubric target scores (mean absolute error ≈ 9.4 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 3: Data science

- **Profile ID:** `ds-scientist-jeddah`
- **User message:** Data science student at KAU in Jeddah looking for data scientist COOP with statistics and Python.

**Parsed profile**

| Field | Value |
|---|---|
| major | DS |
| city | Jeddah |
| skills | python; sql; numpy |
| interest | Data Science |
| program_type | COOP |
| work_mode | Hybrid |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Lucidya | Technical Internship or Coop – Lucidya | Machine Learning | 69.8 | 64.1 | 5.8 |
| 2 | HungerStation | هنقرستيشن | Co-OP Trainee, Data Analysis – Info Sec | Data Analytics | 63.8 | 66.4 | 2.6 |
| 3 | OmniOps | Co‑op Training Program | Data Science | 62.8 | 62.0 | 0.8 |
| 4 | Gathern | Co-op Program | Software Engineering | 62.8 | 60.7 | 2.1 |
| 5 | Saudi Motorsport Company (SMC) | COOP Trainee (IT Asset Project Management) | General Computing | 62.3 | 54.2 | 8.2 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (python; sql; numpy) and interest (Data Science) and location preference (Jeddah), surfacing clusters such as Machine Learning, Data Analytics, Data Science.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were close to rubric target scores (mean absolute error ≈ 3.9 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 4: AI / machine learning

- **Profile ID:** `ds-remote-coop`
- **User message:** DS student seeking remote COOP in machine learning and data analysis.

**Parsed profile**

| Field | Value |
|---|---|
| major | DS |
| city | — |
| skills | python; pandas; scikit-learn |
| interest | — |
| program_type | COOP |
| work_mode | Remote |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | OmniOps | Co‑op Training Program | Data Science | 62.3 | 61.0 | 1.4 |
| 2 | Gathern | Co-op Program | Software Engineering | 62.3 | 58.7 | 3.6 |
| 3 | EjadTech - إيجاد التقنية | Summer Internship Program 2025 (Computer, Data, and AI Majors) | Software Engineering | 55.8 | 53.6 | 2.2 |
| 4 | Bosch Middle East | Software Development Intern (AI/Cloud) | Data Science | 54.3 | 60.1 | 5.8 |
| 5 | MOZN | Data Science Intern | Data Science | 54.3 | 54.1 | 0.2 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (python; pandas; scikit-learn), surfacing clusters such as Data Science, Software Engineering.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were close to rubric target scores (mean absolute error ≈ 2.6 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 5: Cloud / data engineering (Dammam)

- **Profile ID:** `de-cloud-dammam`
- **User message:** Data engineer student in Dammam targeting cloud and big data training with AWS.

**Parsed profile**

| Field | Value |
|---|---|
| major | DE |
| city | Dammam |
| skills | python; sql |
| interest | — |
| program_type | Training |
| work_mode | Hybrid |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Tabby | Intern Data Engineer | Data Engineering | 61.8 | 57.1 | 4.7 |
| 2 | Laverne Group | مجموعة لافيرن | Data Analyst / Data Engineer Intern (IT Department) | Data Analytics | 59.8 | 57.5 | 2.3 |
| 3 | Tabby | Intern DevOps Engineer | DevOps | 59.5 | 57.7 | 1.8 |
| 4 | Tabby | Intern Backend (GO) Engineer | Software Engineering | 58.8 | 56.3 | 2.5 |
| 5 | Bank Albilad | Cooperative & Summer Training Program | Network Engineering | 56.8 | 45.3 | 11.5 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (python; sql) and location preference (Dammam), surfacing clusters such as Data Engineering, Data Analytics, DevOps.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were moderate to rubric target scores (mean absolute error ≈ 4.6 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 6: Network engineering (Dhahran)

- **Profile ID:** `ce-network-dhahran`
- **User message:** Computer engineering student at KFUPM in Dhahran seeking network engineer COOP.

**Parsed profile**

| Field | Value |
|---|---|
| major | CE |
| city | Dhahran |
| skills | linux; c++ |
| interest | Computer Engineering |
| program_type | COOP |
| work_mode | On-site |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Schneider Electric | Co-op Intern (Engineering) - Al Khobar (Jan–Aug 2026) | Network Engineering | 69.0 | 59.9 | 9.1 |
| 2 | Bank Albilad | Cooperative & Summer Training Program | Network Engineering | 67.0 | 61.4 | 5.6 |
| 3 | Yasref | Yasref Cooperative Training Program | Network Engineering | 65.0 | 56.2 | 8.8 |
| 4 | Saudi Tadawul Group | تداول | Cooperative Training Program (COOP) | Software Engineering | 62.0 | 67.4 | 5.4 |
| 5 | Saudi Standards, Metrology and Quality Organization (SASO) | Cooperative Training (Collaborative Training) | Network Engineering | 62.0 | 56.2 | 5.8 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (linux; c++) and interest (Computer Engineering) and location preference (Dhahran), surfacing clusters such as Network Engineering.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were moderate to rubric target scores (mean absolute error ≈ 7.0 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 7: Strong prediction (low error)

- **Profile ID:** `ds-gpa-ielts`
- **User message:** Data science student with GPA 4.5 and IELTS looking for internship in Riyadh.

**Parsed profile**

| Field | Value |
|---|---|
| major | DS |
| city | Riyadh |
| skills | sql; python |
| interest | — |
| program_type | Internship |
| work_mode | On-site |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Laverne Group | مجموعة لافيرن | Data Analyst / Data Engineer Intern (IT Department) | Data Analytics | 70.7 | 64.2 | 6.5 |
| 2 | Tabby | Intern Data Engineer | Data Engineering | 65.7 | 62.5 | 3.2 |
| 3 | MOZN | Data Science Intern | Data Science | 65.7 | 59.3 | 6.4 |
| 4 | Bosch Middle East | Software Development Intern (AI/Cloud) | Data Science | 64.7 | 65.4 | 0.7 |
| 5 | Boeing Saudi Arabia Limited | Intern - Info Technology & Data Analytics (Riyadh) | Data Analytics | 63.7 | 64.2 | 0.5 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (sql; python) and location preference (Riyadh), surfacing clusters such as Data Analytics, Data Engineering, Data Science.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were close to rubric target scores (mean absolute error ≈ 3.5 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.

## Example 8: Weak prediction (high error)

- **Profile ID:** `remote-only-de`
- **User message:** Data engineering student seeking fully remote training anywhere in Saudi Arabia.

**Parsed profile**

| Field | Value |
|---|---|
| major | DE |
| city | Remote |
| skills | python; sql |
| interest | — |
| program_type | Training |
| work_mode | Remote |

**Top 5 opportunities (by rubric target score)**

| Rank | Company | Program | Role cluster | Target | Predicted | |AE| |
|---:|---|---|---|---:|---:|---:|
| 1 | Meel | ميل | Software Developer Internship (Remote, min 2 months) | Software Engineering | 63.5 | 61.4 | 2.1 |
| 2 | AFNOYS | AI Automation Intern - KSA (Remote, 4 weeks) | General Computing | 63.5 | 58.4 | 5.1 |
| 3 | Tabby | Intern Backend (GO) Engineer | Software Engineering | 61.5 | 61.4 | 0.1 |
| 4 | Saudi National Bank (SNB) | SNB Cooperative Training Program | General Computing | 58.5 | 49.1 | 9.4 |
| 5 | Al Rajhi Bank | Cooperative Training Program | General Computing | 58.5 | 46.0 | 12.5 |

**Interpretation**

- **What matched:** The rubric-ranked top opportunities align with listed skills (python; sql) and location preference (Remote), surfacing clusters such as Software Engineering, General Computing.
- **What was missing:** Some top rubric picks are generic COOP listings with thin skill metadata, so the model must infer fit mainly from text rather than structured skill overlap.
- **Prediction quality:** On this hold-out profile, fair-model predictions were moderate to rubric target scores (mean absolute error ≈ 5.9 on the top 5).
- **Takeaway:** This shows the honest ML track can rank plausible opportunities from profile text, but it is not yet wired into the live `/recommend` endpoint — rubric scoring still drives production ranking.
