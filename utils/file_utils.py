import glob
import json
import os

from logs.logger import logger


def merge_output_chunks(
    output_pattern="output_chunk_*.json", merged_file="output.json"
):
    logger.info(
        f"Merging chunk files matching '{output_pattern}' into '{merged_file}'"
    )

    merged_data = []

    for file_name in sorted(glob.glob(output_pattern)):
        logger.info(f"Reading from {file_name}")
        with open(file_name, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    logger.warning(f"{file_name} did not contain a list")
            except json.JSONDecodeError as e:
                logger.error(f"Could not decode JSON from {file_name}: {e}")

    with open(merged_file, "w", encoding="utf-8") as out_file:
        json.dump(merged_data, out_file, ensure_ascii=False, indent=2)

    logger.info(f"Merged {len(merged_data)} records into '{merged_file}'")


def cleanup_old_chunks(pattern="output_chunk_*.json"):
    for file_path in glob.glob(pattern):
        try:
            os.remove(file_path)
            logger.info(f"Deleted old chunk file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")
