from dataclasses import dataclass


APP_TITLE = "Cable Tension Calculator"
RESULT_FILEPATH = "data/calc_results.xlsx"
MASTER_FILEPATH = "data/cable_master.xlsx"
MASTER_SHEET_NAME = "master"
RESULT_SHEET_NAME = "results"


DEFAULT_MAX_MODE = 7
MAX_SUPPORTED_MODE = 10

DEFAULT_MANUAL_K = 1.0
DEFAULT_MANUAL_B = 0.5

DEFAULT_METHOD = "grid"

DEFAULT_K_MIN = 0.5
DEFAULT_K_MAX = 2.0
DEFAULT_B_MIN = -10.0
DEFAULT_B_MAX = 10.0

DEFAULT_GRID_STEP_K = 0.01
DEFAULT_GRID_STEP_B = 0.1

DEFAULT_WEIGHT_MODE = "none"
DEFAULT_USE_NORMALIZED_MSE = False
DEFAULT_SAVE_RESULT = False


FREQUENCY_COLUMN_PREFIX = "f"
USE_COLUMN_PREFIX = "use_"
OBS_COLUMN_SUFFIX = "_obs"
THEORY_COLUMN_SUFFIX = "_theory"


REQUIRED_MASTER_COLUMNS = [
    "施設名",
    "ケーブルNo.",
    "枝番",
    "単位重量",
    "ケーブル長",
    "設計張力",
]

OPTIONAL_MASTER_COLUMNS = [
    "設計剛性",
    "ξ",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
]