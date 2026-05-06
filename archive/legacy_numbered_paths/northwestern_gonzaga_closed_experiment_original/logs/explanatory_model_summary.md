# Explanatory Team-Strength Model Summary

## Framing
- This is a retrospective explanatory model, not a leakage-free real-time prediction model.
- Shirley variables are temporally downstream of Gonzaga/Northwestern and proxy latent team strength/results context.

## Coverage
- Rows with complete Shirley team-strength features: 444 / 1082
- Validation rows with complete Shirley team-strength features: 71

## Validation Results
                    experiment_name          model_family                                                                                                                                                                                                                                                                                                                                       features_used  complete_case_strength_rows_only  train_rows  validation_rows  validation_accuracy  true_L_pred_L  true_L_pred_W  true_W_pred_L  true_W_pred_W  false_positive_count  false_negative_count
                  majority_baseline              majority                                                                                                                                                                                                                                                                                                                                                none                             False         757              162             0.518519              0             78              0             84                    78                     0
     speech_structure_only_logistic              logistic                                                                                                                                                                                                                                       num_positions, num_adv_inh_solv, num_offs, num_cards_total, num_cards_with_highlight, total_highlighted_words                             False         757              162             0.530864             26             52             24             60                    52                    24
     shirley_strength_only_logistic              logistic                                                                                                                team_place, opponent_place, place_diff, team_winpm, opponent_winpm, winpm_diff, team_pts_pm, opponent_pts_pm, pts_pm_diff, team_osd, opponent_osd, osd_diff, team_ballot_win_count, opponent_ballot_win_count, ballot_win_count_diff                              True         310               71             0.746479             23             10              8             30                    10                     8
  shirley_strength_only_elastic_net           elastic_net                                                                                                                team_place, opponent_place, place_diff, team_winpm, opponent_winpm, winpm_diff, team_pts_pm, opponent_pts_pm, pts_pm_diff, team_osd, opponent_osd, osd_diff, team_ballot_win_count, opponent_ballot_win_count, ballot_win_count_diff                              True         310               71             0.746479             23             10              8             30                    10                     8
   combined_speech_shirley_logistic              logistic num_positions, num_adv_inh_solv, num_offs, num_cards_total, num_cards_with_highlight, total_highlighted_words, team_place, opponent_place, place_diff, team_winpm, opponent_winpm, winpm_diff, team_pts_pm, opponent_pts_pm, pts_pm_diff, team_osd, opponent_osd, osd_diff, team_ballot_win_count, opponent_ballot_win_count, ballot_win_count_diff                              True         310               71             0.704225             22             11             10             28                    11                    10
combined_speech_shirley_elastic_net           elastic_net num_positions, num_adv_inh_solv, num_offs, num_cards_total, num_cards_with_highlight, total_highlighted_words, team_place, opponent_place, place_diff, team_winpm, opponent_winpm, winpm_diff, team_pts_pm, opponent_pts_pm, pts_pm_diff, team_osd, opponent_osd, osd_diff, team_ballot_win_count, opponent_ballot_win_count, ballot_win_count_diff                              True         310               71             0.690141             22             11             11             27                    11                    11
    shirley_strength_calibrated_svm calibrated_linear_svm                                                                                                                team_place, opponent_place, place_diff, team_winpm, opponent_winpm, winpm_diff, team_pts_pm, opponent_pts_pm, pts_pm_diff, team_osd, opponent_osd, osd_diff, team_ballot_win_count, opponent_ballot_win_count, ballot_win_count_diff                              True         310               71             0.746479             24              9              9             29                     9                     9

## Explanatory Power
- Speech-structure-only accuracy: 0.530864
- Shirley/team-strength-only logistic accuracy: 0.746479
- Combined speech + Shirley logistic accuracy: 0.704225
- Combined minus strength-only delta: -0.042254

## Best Model Coefficients
               experiment_name                   feature  coefficient  abs_coefficient
shirley_strength_only_logistic               pts_pm_diff     0.512590         0.512590
shirley_strength_only_logistic               team_pts_pm     0.321601         0.321601
shirley_strength_only_logistic     ballot_win_count_diff     0.318049         0.318049
shirley_strength_only_logistic           opponent_pts_pm    -0.297173         0.297173
shirley_strength_only_logistic              opponent_osd     0.294477         0.294477
shirley_strength_only_logistic                  osd_diff    -0.275196         0.275196
shirley_strength_only_logistic opponent_ballot_win_count    -0.212999         0.212999
shirley_strength_only_logistic            opponent_winpm     0.201190         0.201190
shirley_strength_only_logistic                place_diff     0.169765         0.169765
shirley_strength_only_logistic     team_ballot_win_count     0.167196         0.167196
shirley_strength_only_logistic                winpm_diff    -0.160547         0.160547
shirley_strength_only_logistic            opponent_place     0.108313         0.108313
shirley_strength_only_logistic                team_place    -0.090445         0.090445
shirley_strength_only_logistic                  team_osd    -0.034602         0.034602
shirley_strength_only_logistic                team_winpm     0.019003         0.019003

## Speech Features After Adding Shirley
                 experiment_name                  feature  coefficient  abs_coefficient
combined_speech_shirley_logistic                 num_offs     0.343065         0.343065
combined_speech_shirley_logistic            num_positions     0.219284         0.219284
combined_speech_shirley_logistic  total_highlighted_words    -0.217348         0.217348
combined_speech_shirley_logistic         num_adv_inh_solv    -0.150898         0.150898
combined_speech_shirley_logistic num_cards_with_highlight     0.045037         0.045037
combined_speech_shirley_logistic          num_cards_total     0.018713         0.018713

## Final Interpretation
- Team-strength variables alone explain substantially more validation signal than parser-derived speech structure.
- Speech/document features do not add incremental explanatory value after adding Shirley variables.
- This supports the claim that latent team strength dominates the current parser-derived structural features in retrospective explanation.
