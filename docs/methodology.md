# Detailed methods and reproducibility

## Results

The supplied vintage has 53 months and 96,185 paid hydronic redemptions. Mean applications rose **48.0%** and payments **52.8%** between June 2022–August 2023 and November 2023–April 2024. The fitted application contrast is **908/month** (95% HAC interval 666–1,151); the payment interval includes zero. The same specification restricted to air-to-water applications gives **901/month** (95% HAC interval 667–1,135). These are associations, not identified causal effects. Air-to-water grants rose £5,000 → £7,500; ground-source grants rose £6,000 → £7,500. The combined hydronic series includes shared ground loops and does not represent a uniform £2,500 increase.

Council rates use cumulative payments per 1,000 Census 2021 households. The Census has 331 original districts, harmonised to 318; 316 of 318 BUS districts can be modelled and two are excluded. Four unitary reorganisations use sums of whole predecessor districts. The [Barnsley and Sheffield Boundary Change Order 2024](https://www.legislation.gov.uk/uksi/2024/1328/contents/made) transferred part of Barnsley to Sheffield on 1 April 2025. [ONS Barnsley](https://www.ons.gov.uk/explore-local-statistics/areas/E08000038-barnsley) and [ONS Sheffield](https://www.ons.gov.uk/explore-local-statistics/areas/E08000039-sheffield) confirm replacement codes. Without category counts for the transferred area, old Census codes E08000016/E08000019 cannot safely be relabelled E08000038/E08000039. Both exclusions remain in the audit; `geographic_coverage.csv` records the counts.

| Held-out model | Count MAE | Rate MAE / 1,000 | Mean Poisson deviance |
|---|---:|---:|---:|
| Pooled rate | 184.06 | 2.412 | 159.02 |
| Poisson | 102.14 | 1.536 | 54.94 |
| Negative binomial | 113.19 | 1.696 | 65.74 |
| Gradient boosting | 83.42 | 1.214 | 38.97 |

Nested selection chose gradient boosting in all 5 outer folds. Its evaluated selection-procedure errors are **1.214 payments per 1,000 Census households**, count MAE **83.42 payments**, and mean Poisson deviance **38.97** (unitless). These equal the boosting candidate scores because every inner selection chose that candidate.

Detached-house share has the clearest positive conditional association. Gap rankings are model-sensitive and are leads for investigation, not evidence of policy failure.

## Methods and reproducibility

Python, pandas, NumPy, Matplotlib, statsmodels and scikit-learn support the analysis; Flask, Jinja, custom CSS and vanilla JavaScript provide BUS Insights; Plotly.js supplies interactive charts. Numeric conversion preserves suppression/missingness, geographic joins use codes, and totals reconcile to published figures.

The main interrupted series excludes May 2022's partial launch and September/October 2023's transition. It fits trend, level and slope changes plus one annual harmonic, ending April 2024 before insulation eligibility changed. HAC uses three calendar-month lags, a finite-sample correction and t intervals. Missing-month scores are zero only in the covariance calculation; outcomes are never imputed. Calendar-lag residual correlations replace the earlier gap-compressed diagnostic. Sensitivities vary timing, seasonality, lag and end date.

Poisson and NB2 use log-household offsets. Fixed row-level shares and unit conversions need no fitted preprocessing; no imputation or global scaler is used. NB2 dispersion and boosting's histogram bins are learnt inside each training split. Boosting uses household weights, Poisson loss and fixed parameters. Five saved geographic folds preserve the original holdouts in `data/processed/geographic_cv_folds.csv`; regions are not predictors.

The four candidate scores above share the comparison folds, making the chosen winner's score selection-optimistic. Nested validation now chooses the model using four inner geographic folds within each outer training set, then evaluates that choice on the outer holdout. It reuses the already fitted candidate's outer predictions without using outer outcomes for selection. Inner memberships, model choices, convergence and metrics are exported as `nested_cv_*`. This evaluates the selection procedure for these fixed candidates; it is not an independent final fitted-model test, and earlier exploration and ten broad regions still limit generalisation.

Seed 42, preserved row/fold order, single-thread numerical operations and pinned versions improve repeatability. `outputs/environment.json` records analysis dependencies only. Exact agreement across different library versions or hardware is not guaranteed.

`data/processed/` holds cleaned data and join/boundary audits; `outputs/` holds figures, coefficients, sensitivities, metrics and keyed out-of-fold predictions. The dashboard reads these exports and does not refit models. SHA-256 hashes protect the six raw files. A deliberate data refresh requires a reviewed manifest and fold refresh.

## Sources and limitations

| Official source | Supplied reference and publication |
|---|---|
| [DESNZ/Ofgem BUS](https://www.gov.uk/government/statistics/boiler-upgrade-scheme-statistics-september-2026) | May 2022–Sep 2026; workbook published 29 Oct 2026 |
| [DESNZ/MCS deployment](https://www.gov.uk/government/statistics/heat-pump-deployment-statistics-june-2026) | 2018 Q1–2026 Q2; published 10 Sep 2026 |
| [ONS TS044](https://www.ons.gov.uk/datasets/TS044/editions/2021/versions/4), [TS046](https://www.ons.gov.uk/datasets/TS046/editions/2021/versions/4), [TS054](https://www.ons.gov.uk/datasets/TS054/editions/2021/versions/4) | Census 2021; supplied v4 released 28 Mar 2023, subsequently superseded |
| [DESNZ off-gas estimates](https://www.gov.uk/government/statistics/sub-national-estimates-of-households-not-connected-to-the-gas-network) | Use 2024; cover published 18 Dec 2025 |

### Download the raw data before rerunning the notebook

Raw downloads are excluded from GitHub. Create `data/raw/` and use the official source links above:

| Download | Filename used in this project |
|---|---|
| BUS September 2026: Excel statistics workbook | `Boiler_Upgrade_Scheme_BUS_Statistics_September_2026.xlsx` |
| Heat pump deployment June 2026: tables (Excel) | `heat-pump-deployment-tables-q2-2026.xlsx` |
| Off-gas estimates: 2015 to 2024 workbook (Excel) | `Subnational_estimates_of_properties_not_connected_to_the_gas_network_2015-2024.xlsx` |
| ONS TS044, edition 2021, version 4: CSV | `TS044-2021-4.csv` |
| ONS TS046, edition 2021, version 4: CSV | `TS046-2021-4.csv` |
| ONS TS054, edition 2021, version 4: CSV | `TS054-2021-4.csv` |

For each ONS CSV, select **all households**, **lower tier local authorities**, **England and Wales**, and all available categories (8 accommodation, 13 heating, 9 tenure). Download the supplied historical versions rather than the latest release. The notebook accepts matching filename prefixes, but requires exactly one match per source; avoid duplicate downloads in `data/raw/`.

`outputs/raw_sha256.json` records the six original file hashes. If a publisher has revised a historical download, the notebook will stop rather than silently analyse different data. Compare the source version and contents before deliberately updating that manifest. Do not overwrite existing source files merely to make the hashes pass. Local environment records and temporary review files are excluded from GitHub; package versions remain pinned in `requirements.txt`.

The BUS webpage was inaccessible during original preparation; its metadata comes from the workbook. The other publication pages were accessible. Gas estimates subtract domestic meters from property stock; reference year 2024 relates to mid-May 2024–mid-May 2025 in the [methodology](https://assets.publishing.service.gov.uk/media/6942bbfc143d960161547dcb/subnational-methodology-and-guidance-booklet.pdf).

The [20 September announcement](https://www.gov.uk/government/speeches/pm-speech-on-net-zero-20-september-2023) preceded [implementation on 23 October](https://www.gov.uk/government/news/heat-pump-grants-increased-by-50-per-cent). Later changes include insulation eligibility (8 May 2024), planning (29 May 2025), expanded eligibility (28 April 2026) and off-gas grants (21 July 2026), documented in the BUS workbook. The short pre/post window, anticipation, payment lags, revisions and co-occurring changes prevent strong causal attribution.

Households are an old exposure proxy, not all eligible properties. Regional rates cover matched councils. Income, deprivation, costs and installer supply are missing. Associations are ecological; model gaps do not establish household behaviour or equity. No credible control supports difference-in-differences; arbitrary classification, clustering and invented monthly council histories are omitted. The [ICF/DESNZ evaluation](https://www.gov.uk/government/publications/evaluation-of-the-boiler-upgrade-scheme-2026) reports approximately 74% **whole-scheme** additionality, not the October uplift effect.

## Attribution

Contains public sector information licensed under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

OGL applies except where stated. BUS/deployment geography tables also acknowledge OS and Royal Mail database rights; preserve those notices. The inaccessible BUS webpage's specific licence was not independently checked; its workbook explicitly licenses NSPL under OGL. No claims concern identifiable households.
