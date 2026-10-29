# Boiler Upgrade Scheme: what does the public data suggest?

England and Wales · Data through September 2026 · Independent educational analysis

The government raised the air-to-water heat pump grant from £5,000 to £7,500 on 23 October 2023, following an announcement on 20 September. This project asks whether scheme activity changed and where uptake is lower than area characteristics would suggest.

## Activity increased, but the grant's contribution remains uncertain

Monthly hydronic applications averaged 1,435 in June 2022–August 2023 and 2,124 in November 2023–April 2024: an observed increase of 48.0%. Paid redemptions rose 52.8% across the same windows. Payments follow completed installations, but are dated by payment rather than installation.

After allowing for a fitted trend and a simple seasonal pattern, the model estimates 908 more applications per month than its no-break projection (95% interval 666–1,151). The corresponding payment contrast is -31 per month, with an interval spanning -418 to 356. This does not establish that the grant caused either change. The pre-period is short, behaviour may have changed before implementation, and later scheme changes complicate longer comparisons.

## Council differences warrant investigation

The model sample contains 316 of 318 BUS councils. Regional cumulative uptake ranges from 1.58 to 6.97 payments per 1,000 Census households. Detached housing has the clearest positive adjusted association.

Nested geographic validation selects a model within each training set before evaluating held-out regions. It selected gradient boosting in every fold, giving an error of about 1.21 payments per 1,000 Census households, compared with 2.41 for a simple baseline. Its largest negative rate gaps include Tendring, South Holland, King’s Lynn and West Norfolk. Rankings change between models, so these are leads for local follow-up, not evidence of policy failure or unequal treatment.

## Implication

Recorded demand strengthened around the uplift, but public aggregates cannot reliably isolate its causal effect. Before targeting support, validate local gaps against current eligible-property stock, affordability, installation costs and installer coverage. Census households are an old standardisation measure, not the number of eligible properties; area associations do not describe individual households.

This analysis does not reproduce ICF's evaluation. Its approximately 74% whole-scheme additionality figure is not the effect of the October grant increase. [Sources, methods and attribution](README.md) accompany the [executed notebook](notebooks/01_data_understanding.ipynb).
