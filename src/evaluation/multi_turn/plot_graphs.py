import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os

def generate_graphs(input_csv, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = pd.read_csv(input_csv)
    
    # Set the style for academic papers
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_context("paper", font_scale=1.5)
    
    # 1. Bar Chart: Average Success Rate by Persona
    plt.figure(figsize=(10, 6))
    persona_avg = df.groupby('persona')['success_rate'].mean().sort_values(ascending=False).reset_index()
    
    ax = sns.barplot(x='success_rate', y='persona', data=persona_avg, palette='viridis')
    plt.title('Average Target System Success Rate Across Personas', pad=20, fontsize=16)
    plt.xlabel('Average Success Rate', fontsize=14)
    plt.ylabel('Simulated Persona', fontsize=14)
    plt.xlim(0, 1.0)
    
    # Add value labels
    for i, v in enumerate(persona_avg['success_rate']):
        ax.text(v + 0.01, i, f'{v:.2f}', color='black', va='center')
        
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig_persona_success_rate.pdf'), format='pdf', dpi=300)
    plt.close()
    
    # 2. Heatmap: Top 15 Worst Performing Intents across Personas
    # Find the 15 intents with the lowest overall success rate
    worst_intents = df.groupby('target_intent')['success_rate'].mean().sort_values().head(15).index
    df_worst = df[df['target_intent'].isin(worst_intents)]
    
    # Pivot for heatmap
    pivot_df = df_worst.pivot(index='target_intent', columns='persona', values='success_rate')
    
    plt.figure(figsize=(12, 8))
    sns.heatmap(pivot_df, annot=True, cmap='coolwarm_r', vmin=0, vmax=1, 
                fmt='.1f', linewidths=.5, cbar_kws={'label': 'Success Rate'})
    
    plt.title('Persona Vulnerability Heatmap: Top 15 Failing Intents', pad=20, fontsize=16)
    plt.xlabel('Simulated Persona', fontsize=14)
    plt.ylabel('Target Intent', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig_persona_heatmap.pdf'), format='pdf', dpi=300)
    plt.close()
    
    print(f"Graphs successfully generated in {output_dir}")

if __name__ == "__main__":
    input_csv = "logs/analyzer_output/run_010/thesis_judge_metrics.csv"
    output_dir = "logs/analyzer_output/run_010/graphs"
    generate_graphs(input_csv, output_dir)
