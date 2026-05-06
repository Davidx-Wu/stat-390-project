# Non-Leaky Feature Search Summary

- Locked baseline accuracy: 0.643836
- Best validation accuracy found: 0.671233
- Best experiment: manual_interactions_logistic
- Best features: num_positions, num_adv_inh_solv, num_offs, num_cards_total, num_cards_with_highlight, total_highlighted_words, num_offs_x_num_cards_total, num_offs_x_total_highlighted_words, num_cards_total_x_num_cards_with_highlight, num_positions_x_num_cards_total, num_adv_inh_solv_x_num_cards_total
- Best confusion matrix: true_L_pred_L=8, true_L_pred_W=21, true_W_pred_L=3, true_W_pred_W=41
- False positives for best model: 21
- False negatives for best model: 3
- Reached >70% validation accuracy: False

## Leakage Audit
- Excluded outcome/result fields: `win_loss`, `Ballots`, `WinPm`, `PtsPm`, judge-decision style fields.
- Excluded identity/context fields by default: `team_code`, `opponent`, `judge`, `tournament_name`.
- Excluded ranking features from primary search because Shirley/NDT ranking files appear to include tournament results, not clearly pre-round rankings.

## Recommendation
- A non-leaky candidate beat the locked baseline, but validate carefully because the validation set is small.
- Treat failures to exceed 70% as evidence that feature quality/noise remains the bottleneck.

## Highest-Confidence Mistakes Preview
- Michigan State FM vs Texas FL, round 5, actual=L, predicted=W, p_win=0.7081235023253504
- Michigan ES vs Emory GS - ONLINE, round 8, actual=L, predicted=W, p_win=0.6931844336676287
- Stanford LY vs Emory CS - ONLINE, round 1, actual=L, predicted=W, p_win=0.6885268395797423
- Emory LY vs Michigan BP, round 3, actual=L, predicted=W, p_win=0.6776853571303043
- Dartmouth CG vs UTD PR, round 5, actual=L, predicted=W, p_win=0.6547023112767398
