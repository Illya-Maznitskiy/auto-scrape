CREATE TABLE cars (
    id SERIAL PRIMARY KEY,
    url TEXT,
    title TEXT,
    price_usd INTEGER,
    odometer INTEGER,
    username TEXT,
    phone_number TEXT,
    image_url TEXT,
    images_count INTEGER,
    car_number TEXT,
    car_vin VARCHAR(50) UNIQUE NOT NULL,
    datetime_found TIMESTAMP
);