import time
import logging
from dotenv import load_dotenv
load_dotenv()

from pipeline.config import Config
from pipeline.reader import load_data
from pipeline.validator import validate_data
from pipeline.processor import process_data
from pipeline.backup_validator import backup_validate
from pipeline.writer import write_data
from pipeline.reporting import generate_report

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def run_pipeline(file_name: str = "inventory_data.csv") -> None:
    start_time = time.time()

    print("\n" + "*" * 50 + "\nESTABLISHED DATA VALIDATION RULES\n" + "*" * 50)
    for k, v in Config.VALIDATION_RULES.items():
        print(f"  - {k}: {v}")

    # Stage 1: Read
    raw_df = load_data(file_name)
    total_raw = len(raw_df)

    # Stage 2: Validate
    validated_df = validate_data(raw_df)

    # Stage 3: Process
    processed_df = process_data(validated_df)

    # Stage 4: Back-up Validate
    final_df = backup_validate(processed_df)

    # Stage 5: Write
    stem = file_name.rsplit(".", 1)[0]
    output_name = f"{stem}_processed.csv"
    write_data(final_df, output_name)

    # Stage 6: Report
    report_path = generate_report(final_df, Config.OUTPUT_DIR / f"{stem}_report.html")

    elapsed = time.time() - start_time
    print(f"\n{'*' * 50}\nFINAL REPORT\n{'*' * 50}")
    print(f"  Raw Input:    {total_raw:,}")
    print(f"  Final Output: {len(final_df):,}")
    print(f"  Report:       {report_path}")
    print(f"  Process Time: {elapsed:.2f}s")
    print("*" * 50 + "\n")


if __name__ == "__main__":
    run_pipeline()
