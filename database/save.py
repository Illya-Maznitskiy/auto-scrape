import json
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

        for i, record in enumerate(records, 1):
            record["price_usd"] = (
                int(record["price_usd"]) if record["price_usd"] else None
            )
            record["odometer"] = (
                int(record["odometer"]) if record["odometer"] else None
            )

            if record.get("datetime_found"):
                dt = parser.parse(record["datetime_found"])
                # Convert aware datetime to naive UTC datetime
                if dt.tzinfo is not None:
                    dt = dt.astimezone(tz=None).replace(tzinfo=None)
                record["datetime_found"] = dt
            else:
                record["datetime_found"] = None

            await conn.execute(
                """
                INSERT INTO cars (url, title, price_usd, odometer, username,
                                  phone_number, image_url, images_count,
                                  car_number, car_vin, datetime_found)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (car_vin) DO UPDATE SET
                    price_usd = EXCLUDED.price_usd,
                    odometer = EXCLUDED.odometer
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
                f"Saved record {i}/{len(records)}: VIN={record['car_vin']}"
            )

    logger.info("All records saved to database.")
