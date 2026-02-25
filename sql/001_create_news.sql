-- Create the news table if it doesn't exist yet.
-- Run this on your PostgreSQL instance before starting the server.

CREATE TABLE IF NOT EXISTS news (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(300)  NOT NULL,
    body          TEXT          NOT NULL,
    published_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Optional: seed a few sample rows for testing
INSERT INTO news (title, body, published_at) VALUES
    ('Breaking: AI passes bar exam',
     'An AI model achieved a perfect score on the bar exam today.',
     '2026-02-24 12:00:00+00'),
    ('New solar farm opens in Texas',
     'A 500 MW solar farm began producing power in west Texas.',
     '2026-02-23 09:30:00+00'),
    ('Global temperatures hit record high',
     'Scientists report that January 2026 was the hottest month on record.',
     '2026-02-22 15:45:00+00');
