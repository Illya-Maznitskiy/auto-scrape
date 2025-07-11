import json

import asyncpg
from dateutil import parser

from database.connection import Database
from logs.logger import logger


async def save_json_to_db(json_file, db: Database):
    """Load JSON records and save them asynchronously to database."""
    logger.info(f"Loading JSON file: {json_file}")

    async with db.pool.acquire() as conn:
        with open(json_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        logger.info(f"Loaded {len(records)} records from JSON.")

        seen_urls = set()
        unique_records = []

        for idx, record in enumerate(records):
            # Normalize and prepare fields
            record["price_usd"] = (
                int(record["price_usd"]) if record.get("price_usd") else None
            )
            record["odometer"] = (
                int(record["odometer"]) if record.get("odometer") else None
            )

            if record.get("datetime_found"):
                dt = parser.parse(record["datetime_found"])
                if dt.tzinfo is not None:
                    dt = dt.astimezone(tz=None).replace(tzinfo=None)
                record["datetime_found"] = dt
            else:
                record["datetime_found"] = None

            url = record.get("url", "").strip()

            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_records.append(record)
            else:
                logger.warning(
                    f"Skipped duplicate record at index {idx} "
                    f"with URL={url or 'N/A'}"
                )

        logger.info(
            f"{len(unique_records)} unique records will be saved to DB."
        )

        for i, record in enumerate(unique_records, 1):
            try:
                await conn.execute(
                    """
                    INSERT INTO cars (url, title, price_usd,
                                      odometer, username,
                                      phone_number, image_url,
                                      images_count,
                                      car_number, car_vin,
                                      datetime_found)
                    VALUES ($1, $2, $3, $4, $5,
                            $6, $7, $8, $9, $10, $11)
                    """,
                    record["url"],
                    record["title"],
                    record["price_usd"],
                    record["odometer"],
                    record["username"],
                    record["phone_number"],
                    record["image_url"],
                    record["images_count"],
                    record["car_number"],
                    record["car_vin"],
                    record["datetime_found"],
                )
                logger.info(
                    f"Saved record {i}/{len(unique_records)}: "
                    f"URL={record['url']}"
                )

            except asyncpg.exceptions.UniqueViolationError:
                logger.warning(
                    f"Skipped DB duplicate at insert time: "
                    f"index={i}, URL={record['url']}"
                )

    logger.info("All unique records saved to database.")
