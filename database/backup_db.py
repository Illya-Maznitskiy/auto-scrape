import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "auto_scrape")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DUMP_FOLDER = os.getenv("DUMP_FOLDER", "dumps")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_backup():
    if not os.path.exists(DUMP_FOLDER):
        os.makedirs(DUMP_FOLDER)
        logger.info(f"Created dump folder at {DUMP_FOLDER}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_filename = f"{DUMP_FOLDER}/backup_{timestamp}.sql"

    # Build pg_dump command
    pg_dump_cmd = [
        "pg_dump",
        f"--host={DB_HOST}",
        f"--port={DB_PORT}",
        f"--username={DB_USER}",
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        DB_NAME,
        "-f",
        dump_filename,
    ]

    # Set PGPASSWORD env var for authentication
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD

    logger.info(f"Starting DB backup to {dump_filename}")
    try:
        subprocess.run(pg_dump_cmd, env=env, check=True)
        logger.info("Database backup completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup failed: {e}")


if __name__ == "__main__":
    create_backup()
