import csv
import uuid
from pathlib import Path

# Pfade anpassen falls nötig
INPUT_CSV_PATH = Path("../dataset/banking77_test.csv")
OUTPUT_CSV_PATH = Path("../dataset/banking77_test_with_uuid.csv")


def add_uuid_to_csv(input_path: Path, output_path: Path):
    if not input_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {input_path}")

    print(f"Lese CSV-Datei: {input_path}...")

    with open(input_path, mode="r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []

        # Fügt 'id' an der ersten Stelle der Spaltenköpfe ein (falls noch nicht vorhanden)
        if "id" not in fieldnames:
            fieldnames.insert(0, "id")

        rows = []
        for row in reader:
            # Generiert eine neue UUID4
            row["id"] = str(uuid.uuid4())
            rows.append(row)

    print(f"Schreibe {len(rows)} Einträge mit UUIDs in: {output_path}...")

    with open(output_path, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Erfolgreich abgeschlossen!")


if __name__ == "__main__":
    add_uuid_to_csv(INPUT_CSV_PATH, OUTPUT_CSV_PATH)