import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bloodlogger.db')

def add_cohort(name, description=None):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO cohorts (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        return cur.lastrowid

def list_cohorts():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, date_created FROM cohorts")
        return cur.fetchall()

def add_sample(cohort_id, animal_id, species, sex, notes, barcode_value):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO samples (cohort_id, animal_id, species, sex, notes, barcode_value)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (cohort_id, animal_id, species, sex, notes, barcode_value))
        conn.commit()
        return cur.lastrowid

def list_samples():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, cohort_id, animal_id, species, sex, notes, barcode_value, date_added FROM samples")
        return cur.fetchall()

def main():
    print("Adding a test cohort...")
    cohort_id = add_cohort("Test Cohort", "This is a test cohort.")
    print(f"Cohort added with ID: {cohort_id}")

    print("Listing all cohorts:")
    for row in list_cohorts():
        print(row)

    print("Adding a test sample...")
    sample_id = add_sample(cohort_id, "A001", "Mouse", "F", "Healthy", "A001BARCODE")
    print(f"Sample added with ID: {sample_id}")

    print("Listing all samples:")
    for row in list_samples():
        print(row)

if __name__ == "__main__":
    main()
