import csv
import argparse
import sys
from pathlib import Path

# =====================================================================
# 1. DEFINE YOUR GLOBAL LABEL MAP HERE (OPTIONAL BULK RENAME)
# =====================================================================
# Format: {"old_label_name": "new_label_name"}
GLOBAL_LABEL_MAP = {
    "reverted_card_payment?": "reverted_card_payment",
    "get_physical_card": "get_pin",
    # Add additional global replacements here if needed...
}


# =====================================================================
# 2. UPDATE LOGIC
# =====================================================================

def update_dataset(input_csv: str, output_csv: str, old_label: str = None, new_label: str = None):
    input_path = Path(input_csv)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    # Build the label map from CLI args or fallback to GLOBAL_LABEL_MAP
    label_map = dict(GLOBAL_LABEL_MAP)
    if old_label and new_label:
        label_map[old_label.strip()] = new_label.strip()

    if not label_map:
        print("[ERROR] No label changes specified! Pass --old_label and --new_label or set GLOBAL_LABEL_MAP.")
        sys.exit(1)

    print(f"Reading dataset from: {input_path}")
    print("Active Label Renaming Map:")
    for src, dst in label_map.items():
        print(f"  - '{src}' => '{dst}'")

    updated_count = 0

    with open(input_path, mode="r", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        if not fieldnames:
            print("[ERROR] The CSV is empty or has no headers.")
            sys.exit(1)

        # Auto-detect the Label column
        label_col = next((col for col in ["label_text", "label", "intent", "category", "target"] if col in fieldnames),
                         None)

        if not label_col:
            print(f"[ERROR] Could not automatically detect Label column in headers: {fieldnames}")
            sys.exit(1)

        print(f"Detected Label column: '{label_col}'")

        rows = []
        for row in reader:
            current_label = row[label_col].strip()

            # Check if this row's label matches a key in our rename map
            if current_label in label_map:
                target_label = label_map[current_label]
                if current_label != target_label:
                    row[label_col] = target_label
                    updated_count += 1

            rows.append(row)

    # Write the updated rows to the output file
    with open(output_csv, mode="w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary Output
    print("\n=======================================")
    print(" UPDATE SUMMARY")
    print("=======================================")
    print(f" Total rows in dataset: {len(rows)}")
    print(f" Rows updated: {updated_count}")
    print(f" File saved to: {output_csv}")


# =====================================================================
# 3. CLI ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename an entire label category across a CSV dataset.")
    parser.add_argument("--input", type=str, required=True, help="Path to the original CSV file.")
    parser.add_argument("--output", type=str, default="dataset_updated.csv", help="Path to save the updated CSV file.")
    parser.add_argument("--old_label", type=str, default=None,
                        help="The exact old label string to replace across all rows.")
    parser.add_argument("--new_label", type=str, default=None, help="The new label string to assign.")

    args = parser.parse_args()

    update_dataset(args.input, args.output, args.old_label, args.new_label)