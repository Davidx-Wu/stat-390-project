# What Actually Worked Memo

The project’s strongest clean predictive evidence comes from a small set of parser-derived structured speech features. The v3 structured logistic baseline reached `0.616438` validation accuracy, slightly above the majority baseline of `0.602740`. Adding interaction-only degree-2 terms and tuning logistic regularization to `C=0.5` improved the clean Gonzaga-only validation accuracy to `0.643836`, making it the locked final predictive model.

What worked was not model complexity. Random forests, gradient boosting, hist gradient boosting, full degree-2 polynomial features, class-weight balancing, side features, density features, semantic highlighted-text features, and paired-round learned models all failed to produce a more credible final predictive result. The consistent pattern is that the dataset is small/noisy enough that higher-capacity models and broader feature expansion tend to hurt generalization rather than help.

The closed Northwestern+Gonzaga experiment changed the story from simple prediction to robustness. When Northwestern was added, validation accuracy dropped sharply: the closed structured logistic model reached `0.530864`, and the manual interaction model reached `0.524691`. That result suggests the Gonzaga-only signal is real but tournament-dependent.

The retrospective Shirley/team-strength models worked much better, with Shirley-only logistic reaching `0.746479` validation accuracy on covered rows. However, those variables are downstream/post-tournament proxies and should not be treated as valid real-time prediction features. Their value is explanatory: they show that latent team strength explains substantially more outcome variation than parser-derived speech structure.

The final Week 5 interpretation is therefore disciplined: structured debate-document features contain modest predictive signal, interaction terms help a little, cross-tournament generalization is weak, and latent team strength dominates in retrospective explanation.
