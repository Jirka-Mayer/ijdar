import os
from pathlib import Path


SMC_FOLDER_PATH = Path(__file__).parent.parent.parent.absolute()
"""Absolute path to the 'smc' folder (the root of this python package)"""

SMASHCIMA_ASSETS_PATH = Path(
    os.environ.get("MC_ASSETS_CACHE", SMC_FOLDER_PATH / "smashcima_assets")
)
"""Path to the cache directory for smashcima assets"""

# redirect smashcima assets
# (must happen before smashcima is imported)
os.environ["MC_ASSETS_CACHE"] = str(SMASHCIMA_ASSETS_PATH)
