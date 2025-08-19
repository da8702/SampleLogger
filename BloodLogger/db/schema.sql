-- Cohorts table
CREATE TABLE IF NOT EXISTS cohorts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    date_created TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Samples table
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cohort_id INTEGER,  -- allow NULL
    animal_id TEXT NOT NULL,
    species TEXT,
    sex TEXT,
    notes TEXT,
    barcode_value TEXT UNIQUE NOT NULL,
    date_added TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cohort_id) REFERENCES cohorts(id) ON DELETE CASCADE
);
