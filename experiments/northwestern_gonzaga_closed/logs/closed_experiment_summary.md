# Northwestern + Gonzaga Closed Experiment Summary

## Inputs
- Northwestern preview: C:\Users\thatd\Desktop\1 -- Statistics\Stat390DataScienceProject\stat-390-project\experiments\northwestern_gonzaga_closed\diagnostics\northwestern_doc_selection_preview.csv
- Northwestern Tabroom CSV: C:\Users\thatd\Desktop\1 -- Statistics\Stat390DataScienceProject\stat-390-project\experiments\northwestern_gonzaga_closed\data_raw\Northwestern_Tabroom-prelims_table.csv
- Gonzaga closed copy source: C:\Users\thatd\Desktop\1 -- Statistics\Stat390DataScienceProject\stat-390-project\data\processed\gonzaga_speech_dataset_v1.csv

## Northwestern Build
- Docs selected: 665
- Docs parsed successfully: 665
- Parse failures: 0
- Rows joined to Tabroom outcomes: 598
- Join failures: 67
- Usable Northwestern rows with non-null outcome: 598
- Northwestern win/loss distribution: {'W': 309, 'L': 289}

## Combined Dataset
- Combined rows: 1082
- Split sizes: {'train': 757, 'test': 163, 'validation': 162}

## Validation Results
- majority_baseline: validation_accuracy=0.518519, validation_rows=162
- structured_logistic: validation_accuracy=0.530864, validation_rows=162
- manual_interaction_logistic: validation_accuracy=0.524691, validation_rows=162

## Interpretation
- Manual interactions did not improve over structured logistic in the closed combined validation split.
- This is a closed robustness check, not final test-set evidence.
