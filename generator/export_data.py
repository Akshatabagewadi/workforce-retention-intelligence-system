
import csv
import json
import hashlib
from pathlib import Path
from datetime import date, datetime

from database.db import SessionLocal
from database.models import (
    Role,
    Team,
    Employee,
    TenureSnapshot,
    EngagementSurvey,
    WorkloadSnapshot,
    CompensationBand,
    PromotionHistory,
    AttritionOutcome,
    Intervention,
)


# ==========================================
# CONFIGURATION
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPORT_DIR = PROJECT_ROOT / "outputs" / "exports"

VALIDATION_REPORT = (
    PROJECT_ROOT / "outputs" / "validation_report.txt"
)

SEED = 20261022

MODELS = [
    Role,
    Team,
    Employee,
    TenureSnapshot,
    EngagementSurvey,
    WorkloadSnapshot,
    CompensationBand,
    PromotionHistory,
    AttritionOutcome,
    Intervention,
]


# ==========================================
# DATA CONVERSION
# ==========================================

def convert_value(value):

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def get_model_data(db, model):

    query = db.query(model)

    primary_keys = [
        column.name
        for column in model.__table__.primary_key.columns
    ]

    for key in primary_keys:
        query = query.order_by(getattr(model, key))

    records = query.all()

    columns = [
        column.name
        for column in model.__table__.columns
    ]

    data = []

    for record in records:

        row = {}

        for column in columns:

            value = getattr(record, column)

            row[column] = convert_value(value)

        data.append(row)

    return columns, data


# ==========================================
# CSV EXPORT
# ==========================================

def export_csv(table_name, columns, records):

    file_path = EXPORT_DIR / f"{table_name}.csv"

    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(records)

    print("CSV created:", file_path.name)

    return file_path


# ==========================================
# JSON EXPORT
# ==========================================

def export_json(table_name, records):

    file_path = EXPORT_DIR / f"{table_name}.json"

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("JSON created:", file_path.name)

    return file_path


# ==========================================
# SQL VALUE CONVERSION
# ==========================================

def sql_value(value):

    if value is None:
        return "NULL"

    if isinstance(value, bool):
        return "1" if value else "0"

    if isinstance(value, (int, float)):
        return str(value)

    value = str(value)

    value = value.replace("'", "''")

    return f"'{value}'"


# ==========================================
# SQL SEED EXPORT
# ==========================================

def export_sql(all_data):

    file_path = EXPORT_DIR / "workforce_seed.sql"

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("-- Workforce Retention Intelligence System\n")
        file.write("-- Generated SQL seed data\n")
        file.write("-- Fixed seed: 20261022\n\n")

        file.write("PRAGMA foreign_keys = ON;\n\n")

        for model in MODELS:

            table_name = model.__tablename__

            columns, records = all_data[table_name]

            if not records:
                continue

            quoted_columns = ", ".join(
                f'"{column}"'
                for column in columns
            )

            file.write(f"-- Table: {table_name}\n")

            for record in records:

                values = ", ".join(
                    sql_value(record[column])
                    for column in columns
                )

                statement = (
                    f'INSERT INTO "{table_name}" '
                    f'({quoted_columns}) '
                    f'VALUES ({values});\n'
                )

                file.write(statement)

            file.write("\n")

    print("SQL created:", file_path.name)

    return file_path


# ==========================================
# SHA-256 CHECKSUM
# ==========================================

def calculate_checksum(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):

            sha256.update(chunk)

    return sha256.hexdigest()


# ==========================================
# VALIDATION SUMMARY
# ==========================================

def export_validation_summary():

    destination = EXPORT_DIR / "validation_summary.txt"

    if VALIDATION_REPORT.exists():

        destination.write_text(
            VALIDATION_REPORT.read_text(
                encoding="utf-8"
            ),
            encoding="utf-8"
        )

        print("Validation summary copied.")

    else:

        destination.write_text(
            "Validation report was not found.\n",
            encoding="utf-8"
        )

        print("WARNING: Validation report not found.")

    return destination


# ==========================================
# SOURCE MANIFEST
# ==========================================

def export_manifest(file_paths, record_counts):

    manifest = {
        "project": "Workforce Retention Intelligence System",
        "description": (
            "Explainable AI-powered employee engagement "
            "and retention analytics platform"
        ),
        "random_seed": SEED,
        "observation_date": "2026-10-30",
        "horizon_end_date": "2027-04-30",
        "database": "SQLite",
        "source": "Existing workforce_retention.db",
        "database_modified": False,
        "record_counts": record_counts,
        "exports": []
    }

    for file_path in file_paths:

        manifest["exports"].append({
            "file": file_path.name,
            "size_bytes": file_path.stat().st_size,
            "sha256": calculate_checksum(file_path)
        })

    manifest_path = EXPORT_DIR / "source_manifest.json"

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4
        )

    print("Source manifest created.")

    return manifest_path


# ==========================================
# MAIN EXPORT FUNCTION
# ==========================================

def export_all_data():

    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    db = SessionLocal()

    try:

        print("\n===================================")
        print("WORKFORCE DATA EXPORT")
        print("===================================")

        all_data = {}
        record_counts = {}
        generated_files = []

        # Read existing database records.

        for model in MODELS:

            table_name = model.__tablename__

            print(f"\nReading {table_name}...")

            columns, records = get_model_data(
                db,
                model
            )

            all_data[table_name] = (
                columns,
                records
            )

            record_counts[table_name] = len(records)

            csv_file = export_csv(
                table_name,
                columns,
                records
            )

            json_file = export_json(
                table_name,
                records
            )

            generated_files.extend([
                csv_file,
                json_file
            ])

        # Generate SQL seed file.

        sql_file = export_sql(all_data)

        generated_files.append(sql_file)

        # Copy validation report.

        validation_file = export_validation_summary()

        generated_files.append(validation_file)

        # Generate source manifest.

        manifest_file = export_manifest(
            generated_files,
            record_counts
        )

        print("\n===================================")
        print("EXPORT COMPLETED SUCCESSFULLY")
        print("===================================")

        print("Tables exported:", len(MODELS))

        print(
            "Total database records:",
            sum(record_counts.values())
        )

        print("Export folder:", EXPORT_DIR)

        print("\nGenerated files:")

        for file_path in generated_files:
            print("-", file_path.name)

        print("-", manifest_file.name)

        print(
            "\nExisting database was only read. "
            "No records were modified."
        )

    finally:

        db.close()


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":

    export_all_data()
