import csv
import argparse
import sys
from pathlib import Path


def create_label_mapping(original_csv: Path) -> dict:
    """Liest den originalen Datensatz und erstellt ein Mapping: Text -> Zahl."""
    if not original_csv.exists():
        print(f"[FEHLER] Originale CSV nicht gefunden: {original_csv}")
        sys.exit(1)

    mapping = {}
    with open(original_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Versuche die Spalten für Text und Zahl automatisch zu finden
        # Im originalen Banking77 heißt der Text oft "category" oder "label_text" und die Zahl "label"
        text_col = next((col for col in ["label_text", "category", "intent"] if col in fieldnames), None)
        num_col = next((col for col in ["label", "label_id", "intent_id"] if col in fieldnames), None)

        if not text_col or not num_col:
            print(f"[FEHLER] Konnte Text- oder Nummern-Spalte im Original nicht finden. Vorhanden: {fieldnames}")
            sys.exit(1)

        for row in reader:
            text_val = row[text_col].strip()
            num_val = row[num_col].strip()
            if text_val not in mapping:
                mapping[text_val] = num_val

    print(f"[OK] {len(mapping)} einzigartige Labels aus dem Original-Datensatz extrahiert.")
    return mapping


def update_synthetic_dataset(synthetic_csv: Path, output_csv: Path, mapping: dict):
    """Fügt dem synthetischen Datensatz die numerische Spalte hinzu."""
    if not synthetic_csv.exists():
        print(f"[FEHLER] Synthetische CSV nicht gefunden: {synthetic_csv}")
        sys.exit(1)

    with open(synthetic_csv, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames)

        # Prüfe, wo der Label-Text steht
        text_col = next((col for col in ["label_text", "category", "intent"] if col in fieldnames), None)
        if not text_col:
            print(f"[FEHLER] Konnte keine Text-Label-Spalte im synthetischen Datensatz finden. Vorhanden: {fieldnames}")
            sys.exit(1)

        # Füge 'label' zu den Headern hinzu, falls es noch nicht existiert
        if "label" not in fieldnames:
            fieldnames.append("label")

        rows = []
        missing_labels = set()

        for row in reader:
            text_val = row[text_col].strip()

            # Hole die numerische Zahl aus dem Mapping
            if text_val in mapping:
                row["label"] = mapping[text_val]
            else:
                # Falls das Label im Original nicht existiert (Tippfehler bei Generierung etc.)
                row["label"] = "-1"
                missing_labels.add(text_val)

            rows.append(row)

    # Speichere die neue CSV ab
    with open(output_csv, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Synthetischer Datensatz erfolgreich aktualisiert: {len(rows)} Zeilen verarbeitet.")
    print(f"[OK] Neue Datei gespeichert unter: {output_csv}")

    if missing_labels:
        print("\n[WARNUNG] Folgende Labels wurden im Original-Datensatz NICHT gefunden und erhielten die ID '-1':")
        for lbl in missing_labels:
            print(f"  - {lbl}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fügt numerische Labels zu einem synthetischen Datensatz hinzu.")
    parser.add_argument("--original", type=str, required=True,
                        help="Pfad zum originalen Datensatz (enthält Text und Nummern)")
    parser.add_argument("--synthetic", type=str, required=True, help="Pfad zum synthetischen Datensatz (nur Text)")
    parser.add_argument("--output", type=str, default="synthetic_with_numeric_labels.csv",
                        help="Pfad für die Ausgabe-CSV")

    args = parser.parse_args()

    # 1. Erstelle das Mapping aus dem Original
    label_map = create_label_mapping(Path(args.original))

    # 2. Aktualisiere den synthetischen Datensatz
    update_synthetic_dataset(Path(args.synthetic), Path(args.output), label_map)