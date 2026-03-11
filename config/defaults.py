from pathlib import Path

DATA_DIR = Path("data")

MASTER_FILEPATH = DATA_DIR / "cable_master.xlsx"
RESULT_FILEPATH = DATA_DIR / "calc_results.xlsx"

MASTER_SHEET_NAME = "master"
RESULT_SHEET_NAME = "results"

APP_TITLE = "Cable Tension Calculator"

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

# ===== Excel列名 =====
FACILITY = "施設名"
CABLE_NO = "ケーブルNo"
BRANCH_NO = "枝番"

UNIT_WEIGHT = "単位重量kg_m"
CABLE_LENGTH = "ケーブル長m"
DESIGN_TENSION = "設計張力kN"
DESIGN_RIGIDITY = "設計剛性Nm2"
XI = "ξ"

FREQUENCY_COLUMN_PREFIX = "f"
USE_COLUMN_PREFIX = "use_"
OBS_COLUMN_SUFFIX = "_obs"
THEORY_COLUMN_SUFFIX = "_theory"

REQUIRED_MASTER_COLUMNS = [
    FACILITY,
    CABLE_NO,
    BRANCH_NO,
    UNIT_WEIGHT,
    CABLE_LENGTH,
    DESIGN_TENSION,
]

OPTIONAL_MASTER_COLUMNS = [
    DESIGN_RIGIDITY,
    XI,
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