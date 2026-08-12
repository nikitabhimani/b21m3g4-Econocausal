# Causal Assumptions — EconoCausal

## 1. Causal Question
Does giving a customer a discount (treatment) cause an increase in their probability
of purchasing (outcome), and how does this effect vary across customers?

## 2. Treatment
`treatment_received` — binary indicator of whether the customer was given any discount.

## 3. Outcome
`purchase` — binary indicator of whether the customer purchased within the campaign window.

## 4. Why These Confounders
The following variables are believed to influence **both** treatment assignment and the
purchase outcome, based on the data-generating process:
- `historical_revenue`, `historical_orders`, `avg_order_value` — higher-value customers are
  both more likely to receive a discount and more likely to purchase.
- `days_since_last_purchase` — recency affects both targeting and purchase likelihood.
- `website_visits`, `email_opens`, `email_clicks` — engagement drives both discount targeting
  and purchase probability.
- `previous_campaign_response` — past responsiveness influences future targeting and outcome.
- `customer_segment` — segment tier directly affects both treatment_logit and baseline_logit
  in the underlying generation process, making it a genuine confounder, not just a covariate.

## 5. Why These Covariates
`age`, `tenure_months`, and `customer_segment` are included as covariates because they help
explain **heterogeneity** in the treatment effect — i.e., they help answer "for which customers
does the discount work better or worse," which is needed for Individual Treatment Effect (ITE)
estimation, not just for removing bias.

## 6. No Unmeasured Confounding Assumption
We assume that, conditional on the observed pre-treatment variables, there are no important
unmeasured confounders. We are making this assumption for the purposes of this analysis —
we are not proving it holds.

**Known limitation:** The underlying data-generating process includes a latent variable,
customer price sensitivity, that influences both treatment assignment and purchase outcome
but is not present in the observed dataset. This is a deliberate, known partial violation of
this assumption, included to make the dataset realistic and to test how robust our Double ML
estimates are to some residual, unobservable confounding.

## 7. Positivity Assumption
We assume every customer has a non-zero probability of both receiving and not receiving the
treatment, given their observed characteristics (i.e., no subgroup is deterministically always
or never treated). This holds by construction in the synthetic data, since treatment is assigned
probabilistically (`treatment_probability`) rather than by hard rule for every customer segment.

## 8. Why Post-Treatment Variables Are Excluded
`purchase_value`, `discount_cost`, `net_revenue`, and `discount_percentage` are excluded from
the confounder/covariate sets because they are determined **after** the treatment is assigned
(or are part of the treatment itself, at finer granularity). Adjusting for post-treatment
variables would introduce post-treatment bias and distort the causal estimate.

## 9. Why true_ite Is Not Used as a Model Feature
`true_ite`, along with `true_baseline_purchase_probability`, `true_treatment_purchase_probability`,
and `true_treatment_probability`, are ground-truth columns generated only for **evaluating** our
model's estimates after training. Using them as model inputs would leak the answer we are trying
to estimate directly into the model, making the exercise meaningless.

## Model
- **Method:** Double Machine Learning (`LinearDML`)
- **Base estimator:** LightGBM