import pandas as pd
import json
from sklearn.metrics import f1_score
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def main():
    base_dir = Path(__file__).parent.parent.parent
    dataset_dir = base_dir / "dataset/single-turn"
    
    # Datasets
    datasets = {
        "GPT-OSS Synthetic Dataset": {
            "csv": "banking77_personas_openai-gpt-oss-120b_clean.csv",
            "log_dir": "logs/single-turn/synthetic-dataset/gpt-oss"
        },
        "Nano Synthetic Dataset": {
            "csv": "banking77_personas_gpt-5.4-nano_clean.csv",
            "log_dir": "logs/single-turn/synthetic-dataset/gpt5"
        },
        "Phi-4 Synthetic Dataset": {
            "csv": "banking77_personas_phi4:14b_clean.csv",
            "log_dir": "logs/single-turn/synthetic-dataset/phi4"
        }
    }
    
    # Evaluators
    models = ["phi4_14b", "mistral-small_24b", "openai-nano", "gemini", "gpt-oss"]
    model_labels = ["Phi-4", "Mistral", "Nano", "Gemini", "GPT-OSS"]
    
    # Order personas to show the gradient (Emotional/Worst -> Formal/Best)
    persona_order = ["angry_layperson", "panicking_emergency", "gen_z_slang", "non_native_speaker", "short_wording", "polite_expert"]
    persona_labels = ["Angry Layperson", "Panicking Emergency", "Gen-Z Slang", "Non-Native Speaker", "Short Wording", "Polite Expert"]

    # Setup the plot with premium aesthetics
    sns.set_theme(style="white", font_scale=1.1)
    
    # 2x2 Grid (zwei oben, eins unten)
    fig = plt.figure(figsize=(15, 12))
    axes = [
        fig.add_subplot(2, 2, 1), 
        fig.add_subplot(2, 2, 2), 
        fig.add_subplot(2, 2, 3)
    ]

    out_dir = base_dir / "chapter_thesis/graphics"
    out_dir.mkdir(parents=True, exist_ok=True)

    for ax, (dataset_name, info) in zip(axes, datasets.items()):
        csv_path = dataset_dir / info["csv"]
        log_dir_path = base_dir / info["log_dir"]
        
        df_csv = pd.read_csv(csv_path)
        
        matrix = []
        for p in persona_order:
            row = []
            for model in models:
                jsonl_path = log_dir_path / f"results-{model}-{csv_path.stem}.jsonl"
                if not jsonl_path.exists():
                    row.append(np.nan)
                    continue
                    
                data = []
                with open(jsonl_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data.append(json.loads(line))
                df_jsonl = pd.DataFrame(data)
                df = pd.merge(df_csv, df_jsonl, on='id')
                
                df_p = df[df['persona'] == p]
                if len(df_p) > 0:
                    f1 = f1_score(df_p['true_intent'], df_p['predicted_intent'], average='macro')
                    row.append(f1)
                else:
                    row.append(np.nan)
            matrix.append(row)
            
        df_matrix = pd.DataFrame(matrix, index=persona_labels, columns=model_labels)
        
        sns.heatmap(df_matrix, ax=ax, annot=True, fmt=".2f", cmap="rocket_r", 
                    cbar=True, vmin=0.4, vmax=0.95, 
                    linewidths=1, linecolor='white',
                    cbar_kws={'label': 'Macro-F1 Score'})
        
        ax.set_title(dataset_name, fontsize=14, pad=15, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.tick_params(axis='y', rotation=0)
        
    plt.tight_layout()
    png_path = out_dir / "persona_heatmap_cross_model.png"
    pdf_path = out_dir / "persona_heatmap_cross_model.pdf"
    plt.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white', transparent=False)
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white', transparent=False)
    print(f"Grafiken gespeichert unter {png_path} und {pdf_path}")

if __name__ == "__main__":
    main()
