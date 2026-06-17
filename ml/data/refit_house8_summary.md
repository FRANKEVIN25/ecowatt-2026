# REFIT House8 Conversion Summary

Source file inspected locally:

`C:\Users\jessz\Downloads\CLEAN_REFIT_081116\CLEAN_House8.csv`

The file matches REFIT Cleaned format:

- Columns: `Time`, `Unix`, `Aggregate`, `Appliance1` to `Appliance9`, `Issues`.
- Rows inspected: 6,118,469.
- Time range: 2013-11-01 22:13:18 to 2015-05-10 23:36:10.
- Sampling: around 8 seconds, consistent with REFIT Cleaned documentation.

The generated file `refit_house8_training.csv` is a 50,000-row converted sample in EcoWatt format. Because the local REFIT folder does not include appliance metadata names, labels are currently generic: `appliance_1` to `appliance_9`.

Real REFIT training test:

- Model: `sgn_refit_house8_v1`
- Epochs: 20
- Accuracy: 0.5255
- Macro F1: 0.3770
- Status: experimental, not committed as final model because it does not meet RNF-02.

Next step: add official House8 appliance names from `CLEAN_READ_ME_081116.txt` or `MetaData_Tables.xlsx`, then build balanced windows before treating REFIT training as final.
