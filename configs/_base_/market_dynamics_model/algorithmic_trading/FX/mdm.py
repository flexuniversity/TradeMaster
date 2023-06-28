market_dynamics_model = dict(
    data_path="data/algorithmic_trading/FX/data.csv",
filter_strength=1,
slope_interval=[-0.05,0.05],
dynamic_number=5,
max_length_expectation=100,
OE_BTC=False,
PM='',
process_datafile_path='',
market_dynamic_modeling_visualization_paths='',
key_indicator='adjcp',
timestamp='date',
tic='tic',
labeling_method='quantile',
min_length_limit=12,
merging_metric='DTW_distance',
merging_threshold=0.005,
merging_dynamic_constraint=1
)