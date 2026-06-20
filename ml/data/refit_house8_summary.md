# REFIT House8 Conversion Summary

Source file inspected locally:

`C:\Users\jessz\Downloads\CLEAN_REFIT_081116\CLEAN_House8.csv`

The file matches REFIT Cleaned format:

- Columns: `Time`, `Unix`, `Aggregate`, `Appliance1` to `Appliance9`, `Issues`.
- Rows inspected: 6,118,469.
- Time range: 2013-11-01 22:13:18 to 2015-05-10 23:36:10.
- Sampling: around 8 seconds, consistent with REFIT Cleaned documentation.

The generated file `refit_house8_training.csv` is a 50,000-row converted sample in EcoWatt format, sampled every 120 valid source rows so it spans from 2013-11-01 to 2015-05-03. Because the local REFIT folder does not include appliance metadata names, labels are currently generic: `appliance_1` to `appliance_9`.

Real REFIT training test:

- Model: `sgn_v2`
- Epochs: 50
- Window size / stride: 60 / 15
- Split: chronological with a 59-row purge gap and zero overlap
- Accuracy: 0.5205
- Macro F1 (classes observed in validation): 0.2737
- Macro F1 (all configured classes): 0.1095
- Status: experimental; the leakage is fixed, but RNF-02 is not met.

Next step: add official House8 appliance names from `CLEAN_READ_ME_081116.txt` or `MetaData_Tables.xlsx`, redesign the window target/balancing so rare appliance events survive the 60-row aggregation, and add independent houses for external validation before treating REFIT training as final.
