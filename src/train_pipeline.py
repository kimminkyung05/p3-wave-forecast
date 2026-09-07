from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_ATMOS_PATH = RAW_DATA_DIR / "train_atmos.csv"
RAW_WAVE_PATH = RAW_DATA_DIR / "train_wave.csv"
TRAIN_PATH = PROCESSED_DATA_DIR / "train.csv"
ANOMALY_CLEANED_PATH = PROCESSED_DATA_DIR / "train_anomaly_cleaned.csv"
FINAL_PATH = PROCESSED_DATA_DIR / "train_final.csv"
PHYSICS_PATH = PROCESSED_DATA_DIR / "train_final_physics.csv"

NUMERIC_COLUMNS = [
    "hs", "tp", "hmax", "wvdir", "wspd",
    "gust", "wdir", "airt", "relh", "caph",
]


def create_merged_train() -> pd.DataFrame:
    """Merge the two supplied raw observation files."""
    atmos = pd.read_csv(RAW_ATMOS_PATH)
    wave = pd.read_csv(RAW_WAVE_PATH)
    atmos["time"] = pd.to_datetime(atmos["time"])
    wave["time"] = pd.to_datetime(wave["time"])

    train = pd.merge(atmos, wave, on=["station", "time"], how="outer")
    train = train.sort_values(["station", "time"]).reset_index(drop=True)

    preferred_order = [
        "case_id", "station", "step_minute", "time", "hs", "tp", "hmax",
        "wvdir", "wspd", "gust", "wdir", "airt", "relh", "caph",
    ]
    existing = [column for column in preferred_order if column in train.columns]
    remaining = [column for column in train.columns if column not in existing]
    train = train[existing + remaining]
    train.to_csv(TRAIN_PATH, index=False)
    return train


def clean_anomalies() -> pd.DataFrame:
    """Apply the original first-pass anomaly rules."""
    cleaned = pd.read_csv(TRAIN_PATH)
    cleaned["time"] = pd.to_datetime(cleaned["time"])

    cleaned.loc[cleaned["hs"] <= 0, "hs"] = np.nan
    cleaned.loc[cleaned["wspd"] < 0, "wspd"] = np.nan
    cleaned.loc[
        (cleaned["caph"] < 950) | (cleaned["caph"] > 1050), "caph"
    ] = np.nan
    cleaned.loc[
        (cleaned["relh"] < 0) | (cleaned["relh"] > 100), "relh"
    ] = np.nan

    for column in ["hs", "wspd", "caph"]:
        is_frozen = (
            (cleaned[column].diff() == 0)
            & (cleaned[column].shift(1).diff() == 0)
            & (cleaned[column].shift(2).diff() == 0)
        )
        cleaned.loc[is_frozen, column] = np.nan

    cleaned.loc[
        cleaned.groupby("station")["hs"].diff().abs() > 2.5, "hs"
    ] = np.nan
    cleaned.loc[cleaned["hmax"] < cleaned["hs"], "hmax"] = np.nan
    cleaned.loc[cleaned["gust"] < cleaned["wspd"], "gust"] = np.nan

    cleaned[NUMERIC_COLUMNS] = cleaned.groupby("station")[NUMERIC_COLUMNS].transform(
        lambda group: group.interpolate(method="linear", limit=2)
    )
    cleaned["hs"] = cleaned["hs"].clip(lower=0.01)
    cleaned["wspd"] = cleaned["wspd"].clip(lower=0.0)
    cleaned.to_csv(ANOMALY_CLEANED_PATH, index=False)
    return cleaned


def create_final_train() -> pd.DataFrame:
    """Apply the original final-pass cleaning and wind-vector calculation."""
    final = pd.read_csv(ANOMALY_CLEANED_PATH)
    final["time"] = pd.to_datetime(final["time"])

    # This order intentionally matches the old two-cell notebook pipeline.
    final["hmax"] = np.maximum(final["hmax"], final["hs"])
    final["gust"] = np.maximum(final["gust"], final["wspd"])
    wind_radians = np.deg2rad(final["wdir"])
    final["u_wind"] = final["wspd"] * np.sin(wind_radians)
    final["v_wind"] = final["wspd"] * np.cos(wind_radians)

    # The old notebook wrote this first final pass to CSV and then read it
    # back before the next pass. Reproduce that serialization boundary in
    # memory so the resulting numeric values remain byte-for-byte identical
    # without creating a temporary output file.
    final_order = [
        "case_id", "station", "step_minute", "time", "hs", "tp", "hmax",
        "wvdir", "wspd", "gust", "wdir", "airt", "relh", "caph",
        "u_wind", "v_wind",
    ]
    existing = [column for column in final_order if column in final.columns]
    remaining = [column for column in final.columns if column not in existing]
    final = final[existing + remaining]
    final = pd.read_csv(StringIO(final.to_csv(index=False)))
    final["time"] = pd.to_datetime(final["time"])

    final = final.sort_values(["station", "time"]).reset_index(drop=True)
    final.loc[final["hs"] <= 0.05, "hs"] = np.nan
    final.loc[final["wspd"] < 0, "wspd"] = np.nan
    final.loc[final["hmax"] < final["hs"], "hmax"] = np.nan
    final.loc[final["gust"] < final["wspd"], "gust"] = np.nan
    final.loc[(final["caph"] < 950) | (final["caph"] > 1050), "caph"] = np.nan

    for _, group in final.groupby("station"):
        index = group.index
        hs_diff = final.loc[index, "hs"].diff().abs()
        final.loc[index[hs_diff > 1.0], "hs"] = np.nan

        rolling_median = (
            final.loc[index, "hs"]
            .rolling(window=5, center=True, min_periods=1)
            .median()
        )
        is_dropout = (rolling_median > 1.5) & (final.loc[index, "hs"] < 0.5)
        final.loc[index[is_dropout], "hs"] = np.nan

    final[NUMERIC_COLUMNS] = final.groupby("station")[NUMERIC_COLUMNS].transform(
        lambda group: group.interpolate(method="linear", limit=2)
    )
    final["hmax"] = np.maximum(final["hmax"], final["hs"])
    final["gust"] = np.maximum(final["gust"], final["wspd"])

    final.to_csv(FINAL_PATH, index=False)
    return final


def add_physics_features(group: pd.DataFrame) -> pd.DataFrame:
    """Add the same physics features and rolling windows as the old notebook."""
    group = group.sort_values("time").copy()
    group["wspd_mean_6h"] = group["wspd"].rolling(36, min_periods=12).mean()
    group["wspd_mean_12h"] = group["wspd"].rolling(72, min_periods=24).mean()
    group["gust_max_6h"] = group["gust"].rolling(36, min_periods=12).max()
    group["gust_max_12h"] = group["gust"].rolling(72, min_periods=24).max()
    group["gust_minus_wspd"] = group["gust"] - group["wspd"]

    angle_difference = np.deg2rad(group["wdir"] - group["wvdir"])
    group["wind_wave_alignment"] = np.cos(angle_difference)
    group["wind_wave_diff"] = np.abs(
        (group["wdir"] - group["wvdir"] + 180) % 360 - 180
    )
    group["caph_change_6h"] = group["caph"] - group["caph"].shift(36)
    group["caph_change_12h"] = group["caph"] - group["caph"].shift(72)
    return group


def create_physics_train() -> pd.DataFrame:
    """Create the model-training data set."""
    physics = pd.read_csv(FINAL_PATH)
    physics["time"] = pd.to_datetime(physics["time"])
    physics = physics.sort_values(["station", "time"]).reset_index(drop=True)

    physics = pd.concat(
        [add_physics_features(group) for _, group in physics.groupby("station")],
        ignore_index=True,
    )
    physics = physics.sort_values(["station", "time"]).reset_index(drop=True)

    wind_radians = np.deg2rad(physics["wdir"])
    physics["u_wind"] = physics["wspd"] * np.sin(wind_radians)
    physics["v_wind"] = physics["wspd"] * np.cos(wind_radians)
    physics.to_csv(PHYSICS_PATH, index=False)
    return physics


def main() -> None:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    train = create_merged_train()
    cleaned = clean_anomalies()
    final = create_final_train()
    physics = create_physics_train()

    expected_columns = [
        "station", "time", "hs", "tp", "hmax", "wvdir", "wspd", "gust", "wdir",
        "airt", "relh", "caph", "u_wind", "v_wind", "wspd_mean_6h",
        "wspd_mean_12h", "gust_max_6h", "gust_max_12h", "gust_minus_wspd",
        "wind_wave_alignment", "wind_wave_diff", "caph_change_6h",
        "caph_change_12h",
    ]
    assert physics.shape == (183600, 23), physics.shape
    assert physics.columns.tolist() == expected_columns, physics.columns.tolist()

    print(f"Saved {TRAIN_PATH}: {train.shape}")
    print(f"Saved {ANOMALY_CLEANED_PATH}: {cleaned.shape}")
    print(f"Saved {FINAL_PATH}: {final.shape}")
    print(f"Saved {PHYSICS_PATH}: {physics.shape}")


if __name__ == "__main__":
    main()
