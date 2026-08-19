import os
import csv
import sys
import queue
import argparse
import numpy as np
import sounddevice as sd
import scipy.signal
from scipy.io import wavfile
from pathlib import Path
from typing import Optional

# ==========================================
# CONFIGURATION
# ==========================================
MIC_RATE = 48000  # Native hardware recording rate (fixes ALSA crash)
TARGET_RATE = 8000  # Target telephony 8kHz rate
CHANNELS = 1  # Mono
DTYPE = 'int16'  # 16-bit PCM

q = queue.Queue()


def audio_callback(indata, frames, time, status):
    """This is called continuously by the audio stream to grab microphone data."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())


def record_audio(output_path: Path, device_id: Optional[int] = None):
    """Handles the start/stop recording logic."""
    # Clear the queue from any previous junk
    while not q.empty():
        q.get()

    #input("\n🎤 Press [ENTER] to START recording...")
    print("🔴 RECORDING... (Press [ENTER] to STOP)")

    try:
        # Open the microphone stream at 48kHz to satisfy the hardware
        with sd.InputStream(samplerate=MIC_RATE, channels=CHANNELS, dtype=DTYPE,
                            device=device_id, callback=audio_callback):
            input()  # Block until user presses Enter again
    except sd.PortAudioError as e:
        print(f"\n[CRITICAL ERROR] Could not connect to the microphone.")
        print(f"Details: {e}")
        print("\nTry running: python -c \"import sounddevice as sd; print(sd.query_devices())\"")
        print("Then restart this script adding: --device <YOUR_MIC_ID>")
        sys.exit(1)

    print("⏹️ Stopped recording.")

    # Gather all audio chunks from the queue
    audio_data = []
    while not q.empty():
        audio_data.append(q.get())

    if not audio_data:
        print("⚠️ No audio data captured.")
        return False

    # Concatenate all chunks
    audio_concat = np.concatenate(audio_data, axis=0)

    # DOWNSAMPLE TO 8kHz (Telephony Standard)
    # Calculate how many total samples we need for 8kHz
    num_seconds = len(audio_concat) / MIC_RATE
    target_samples = int(num_seconds * TARGET_RATE)

    # Resample using scipy and convert back to 16-bit PCM
    resampled_audio = scipy.signal.resample(audio_concat, target_samples)
    resampled_audio = np.int16(resampled_audio)

    # Save to WAV file
    wavfile.write(output_path, TARGET_RATE, resampled_audio)
    return True


def get_already_recorded_uuids(output_csv: Path) -> set:
    """Reads the output CSV to figure out which UUIDs we can skip."""
    if not output_csv.exists():
        return set()

    recorded = set()
    with open(output_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "uuid" in row:
                recorded.add(row["uuid"])
    return recorded


def run_recording_session(input_csv: Path, output_csv: Path, audio_dir: Path, persona: str, device_id: Optional[int]):
    # Ensure audio directory exists
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Figure out what we've already done
    recorded_uuids = get_already_recorded_uuids(output_csv)

    # Read the dataset
    dataset = []
    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Auto-detect headers
        fieldnames = reader.fieldnames or []
        id_col = next((col for col in ["id", "uuid", "sample_id"] if col in fieldnames), None)
        text_col = next((col for col in ["text", "utterance", "query"] if col in fieldnames), None)

        # Explicitly look for label_text and label
        label_text_col = "label_text" if "label_text" in fieldnames else None
        label_num_col = "label" if "label" in fieldnames else None

        if not id_col or not text_col:
            print("[ERROR] Could not auto-detect ID or Text columns in input CSV.")
            sys.exit(1)

        for row in reader:
            dataset.append({
                "uuid": row[id_col].strip(),
                "text": row[text_col].strip(),
                "label_text": row[label_text_col].strip() if label_text_col else "unknown",
                "label": row[label_num_col].strip() if label_num_col else "unknown"
            })

    # Prepare the output CSV with the exact requested fields
    output_exists = output_csv.exists()
    out_fieldnames = ["uuid", "audio_path", "text", "label_text", "label", "persona"]

    print(f"\nLoaded {len(dataset)} sentences. Skipping {len(recorded_uuids)} already recorded.")

    with open(output_csv, "a", encoding="utf-8", newline="") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=out_fieldnames)
        if not output_exists:
            writer.writeheader()

        # Start Interactive Loop
        for item in dataset:
            uuid_val = item["uuid"]
            text_val = item["text"]
            label_text_val = item["label_text"]
            label_num_val = item["label"]

            if uuid_val in recorded_uuids:
                continue

            audio_filename = f"{uuid_val}.wav"
            audio_path = audio_dir / audio_filename

            while True:
                # Clear terminal for clean UI
                os.system('cls' if os.name == 'nt' else 'clear')

                print("======================================================")
                print(f" UUID    : {uuid_val}")
                print(f" Intent  : {label_text_val} (ID: {label_num_val})")
                print(f" Persona : {persona}")
                print("======================================================")
                print(f"\n💬 TEXT TO SPEAK:\n\n\"{text_val}\"\n")
                print("======================================================")

                print("\nOptions:")
                print("  [ENTER] Start recording")
                print("  [s]     Skip this sentence")
                print("  [q]     Quit the session")

                choice = input("\nYour choice: ").strip().lower()

                if choice == 'q':
                    print("Exiting session. Progress saved!")
                    sys.exit(0)
                elif choice == 's':
                    print("Skipped.")
                    break
                elif choice == '':
                    # Run the recording
                    success = record_audio(audio_path, device_id)

                    if success:
                        print(f"\n✅ Audio saved temporarily to {audio_filename} (Downsampled to 8kHz)")

                        # Post-recording options
                        post_choice = input(
                            "\nAction: [ENTER] Accept & Save | [r] Re-record | [q] Quit : ").strip().lower()

                        if post_choice == 'r':
                            continue  # Loops back to re-record the same sentence
                        elif post_choice == 'q':
                            sys.exit(0)
                        else:
                            # Save to CSV including both label names and numbers
                            writer.writerow({
                                "uuid": uuid_val,
                                "audio_path": str(audio_path),
                                "text": text_val,
                                "label_text": label_text_val,
                                "label": label_num_val,
                                "persona": persona
                            })
                            out_f.flush()  # Ensure it writes to disk immediately
                            recorded_uuids.add(uuid_val)
                            break  # Move to next sentence
                else:
                    print("Invalid choice.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Telephony Audio Dataset Recorder (8kHz, Mono)")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV containing sentences.")
    parser.add_argument("--output", type=str, default="recorded_audio_dataset.csv",
                        help="Path to save the output metadata CSV.")
    parser.add_argument("--audio_dir", type=str, default="telephony_audio_files", help="Folder to save the .wav files.")
    parser.add_argument("--persona", type=str, default="Neutral", help="The persona type you are recording as.")
    parser.add_argument("--device", type=int, default=None,
                        help="The audio input device ID (e.g. 4). Run python -m sounddevice to list.")

    args = parser.parse_args()

    run_recording_session(
        input_csv=Path(args.input),
        output_csv=Path(args.output),
        audio_dir=Path(args.audio_dir),
        persona=args.persona,
        device_id=args.device
    )