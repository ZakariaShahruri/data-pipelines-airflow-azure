from dotenv import load_dotenv
load_dotenv()  

import time
import pandas as pd

from pipeline.config import Config
from pipeline.reader import reader
from pipeline.validator import validator
from pipeline.processor import processor
from pipeline.backup_validator import backup_validator
from pipeline.writer import writer


if __name__ == "__main__":
    start_time = time.time()

    # Print validation rules at startup
    print("\n" + "*"*50 + "\nESTABLISHED DATA VALIDATION RULES\n" + "*"*50)
    for k, v in Config.VALIDATION_RULES.items():
        print(f"  - {k}: {v}")

    # ── Stage 1: Read ─────────────────────────────────────────────────────────
    raw_df = reader(Config.INPUT_FILE)
    total_raw_count = len(raw_df)

    # ── Stage 2: Primary Validation ───────────────────────────────────────────
    validated_df, rejected_primary = validator(raw_df)

    # ── Stage 3: Process ──────────────────────────────────────────────────────
    processed_df = processor(validated_df)

    # ── Stage 4: Back-up Validation ───────────────────────────────────────────
    final_df, rejected_backup = backup_validator(processed_df)

    # ── Stage 5: Write ────────────────────────────────────────────────────────
    all_rejected = pd.concat([rejected_primary, rejected_backup], ignore_index=True)
    writer(final_df, invalid_df=all_rejected)

    # ── Final Report ──────────────────────────────────────────────────────────
    print(f"\n{'*'*50}\nFINAL DEFENCE QUALITY REPORT\n{'*'*50}")
    print(f"  Raw Input:          {total_raw_count:,}")
    print(f"  Rejected (primary): {len(rejected_primary):,}")
    print(f"  Rejected (back-up): {len(rejected_backup):,}")
    print(f"  Final Gold:         {len(final_df):,}")
    print(f"  Data Loss Rate:     {((total_raw_count - len(final_df)) / total_raw_count * 100):.2f}%")
    print(f"  Process Time:       {time.time() - start_time:.2f}s")
    print("*"*50 + "\n")