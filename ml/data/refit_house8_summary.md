# REFIT House8 Conversion Summary

Source file inspected locally:

`C:\Users\jessz\Downloads\CLEAN_REFIT_081116\CLEAN_House8.csv`

The file matches REFIT Cleaned format:

- Columns: `Time`, `Unix`, `Aggregate`, `Appliance1` to `Appliance9`, `Issues`.
- Rows inspected: 6,118,469.
- Time range: 2013-11-01 22:13:18 to 2015-05-10 23:36:10.
- Sampling: around 8 seconds, consistent with REFIT Cleaned documentation.

The generated file `refit_house8_training.csv` is a 50,000-row converted sample in EcoWatt format, sampled every 120 valid source rows so it spans from 2013-11-01 to 2015-05-03.

Official House 8 metadata is now applied in the conversion and prediction
pipeline:

- `Appliance1`: fridge
- `Appliance2`: freezer
- `Appliance3`: washer dryer
- `Appliance4`: washing machine
- `Appliance5`: toaster
- `Appliance6`: computer
- `Appliance7`: television
- `Appliance8`: microwave
- `Appliance9`: kettle

Source: NILMTK REFIT `building8.yaml`, derived from the REFIT dataset metadata.

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

## SGN v3 correction

The official REFIT/NILMTK channel map is now used for House 8:

- `Appliance4`: washing machine
- `Appliance8`: microwave
- `Appliance9`: kettle

The final personalized checkpoint uses a chronological 60/20/20 split over the
complete 6,118,469-row House 8 file. The final 20% contains 70,875 evaluation
windows and has zero overlap with training or threshold calibration.

- Accuracy: 0.9877
- Macro F1: 0.3475
- Macro balanced accuracy: 0.7619
- Mean MAE: 16.19 W
- Kettle F1: 0.5141
- Washing-machine F1: 0.4196
- Microwave F1: 0.1087
- RNF-02: not passed

This is a substantial and leakage-free improvement over `sgn_v2`, but it is
not presented as production-grade disaggregation. Accuracy is high because
off-state samples dominate; F1 remains the primary acceptance metric.

## Metadata verification retraining

The personalized SGN v3 model was retrained after making the official House 8
metadata explicit in the pipeline and exported checkpoint. The result remained
deterministically unchanged at Macro-F1 `0.3475`, which is expected: SGN v3 was
already trained against the correct physical channels for washing machine,
microwave, and kettle. The metadata correction fixes naming and traceability;
it does not relabel or rebalance those three existing target signals.
