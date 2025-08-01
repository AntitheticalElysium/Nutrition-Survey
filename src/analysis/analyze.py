import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def analyze_results():
    """
    Analyzes nutritional summary files and generates plots.
    """
    script_dir = Path(__file__).parent
    results_dir = script_dir / ".." / ".." / "data" / "results"
    reports_dir = script_dir / ".." / ".." / "reports" / "figures"
    
    # Create reports directory if it doesn't exist
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_summaries = []

    # Load all summary files
    summary_files = list(results_dir.glob("*_nutrition_summary.txt"))
    
    if not summary_files:
        print(f"No summary files found in {results_dir}")
        return

    for summary_file in summary_files:
        print(f"Processing: {summary_file.name}")
        
        try:
            # Read the file and extract nutrient data
            with open(summary_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find the start of nutrient data (after "TOTAL WEEKLY NUTRITIONAL INTAKE:")
            nutrient_start = -1
            for i, line in enumerate(lines):
                if "TOTAL WEEKLY NUTRITIONAL INTAKE:" in line:
                    # Skip the header line and the dashes line
                    nutrient_start = i + 2
                    break
            
            if nutrient_start == -1:
                print(f"Could not find nutrient data section in {summary_file.name}")
                continue
            
            # Parse nutrient data
            data = {}
            for line in lines[nutrient_start:]:
                line = line.strip()
                if not line:  # Skip empty lines
                    break
                
                if ':' in line:
                    parts = line.split(':', 1)  # Split only on first colon
                    if len(parts) == 2:
                        nutrient = parts[0].strip()
                        try:
                            value = float(parts[1].strip())
                            data[nutrient] = value
                        except ValueError:
                            print(f"Could not parse value for {nutrient}: {parts[1]}")
                            continue
            
            if data:
                data['survey_file'] = summary_file.stem.replace('_nutrition_summary', '')
                all_summaries.append(data)
                print(f"Extracted {len(data)-1} nutrients from {summary_file.name}")
            else:
                print(f"No nutrient data found in {summary_file.name}")
                
        except Exception as e:
            print(f"Error processing {summary_file.name}: {e}")
            continue

    if not all_summaries:
        print("No valid summary files found to analyze.")
        return

    # Combine all summaries into a single DataFrame
    df = pd.DataFrame(all_summaries)
    
    # Set survey_file as index for better visualization
    if 'survey_file' in df.columns:
        df = df.set_index('survey_file')
    
    print(f"\nLoaded data for {len(df)} surveys with {len(df.columns)} nutrients")
    print(f"Surveys: {list(df.index)}")

    # Define key nutrients to plot
    key_nutrients = ['proteines', 'lipides', 'glucides', 'fibres', 'sucres', 'calcium', 'fer', 'vitamine_c']
    
    # Filter for nutrients that are actually in the dataframe
    available_nutrients = [n for n in key_nutrients if n in df.columns]
    
    if not available_nutrients:
        print("None of the key nutrients were found in the summary files.")
        print(f"Available nutrients: {list(df.columns)}")
        return

    print(f"Plotting nutrients: {available_nutrients}")

    # Create multiple plots
    
    # 1. Average nutrient intake across all surveys
    df_mean = df[available_nutrients].mean()
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(range(len(df_mean)), df_mean.values)
    plt.title('Average Weekly Nutritional Intake Across All Surveys', fontsize=14, fontweight='bold')
    plt.ylabel('Amount per week', fontsize=12)
    plt.xlabel('Nutrients', fontsize=12)
    plt.xticks(range(len(df_mean)), df_mean.index, rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, value in zip(bars, df_mean.values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + value*0.01,
                f'{value:.1f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    output_path = reports_dir / 'average_nutritional_intake.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved average intake plot to: {output_path}")

    # 2. Comparison between surveys (if multiple surveys)
    if len(df) > 1:
        plt.figure(figsize=(14, 8))
        
        # Select top nutrients with highest average values for better visualization
        top_nutrients = df_mean.nlargest(6).index.tolist()
        
        df_subset = df[top_nutrients]
        
        ax = df_subset.plot(kind='bar', figsize=(12, 6))
        plt.title('Nutritional Intake Comparison Between Surveys', fontsize=14, fontweight='bold')
        plt.ylabel('Amount per week', fontsize=12)
        plt.xlabel('Surveys', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Nutrients', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        output_path = reports_dir / 'survey_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved comparison plot to: {output_path}")

    # 3. Summary statistics
    stats_file = reports_dir / 'nutritional_statistics.txt'
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("=== NUTRITIONAL ANALYSIS SUMMARY ===\n")
        f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Number of Surveys: {len(df)}\n")
        f.write(f"Number of Nutrients Analyzed: {len(available_nutrients)}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("AVERAGE WEEKLY INTAKE:\n")
        f.write("-" * 25 + "\n")
        for nutrient, value in df_mean.items():
            f.write(f"{nutrient}: {value:.2f}\n")
        
        if len(df) > 1:
            f.write("\n\nSTANDARD DEVIATION:\n")
            f.write("-" * 20 + "\n")
            df_std = df[available_nutrients].std()
            for nutrient, value in df_std.items():
                f.write(f"{nutrient}: {value:.2f}\n")
    
    print(f"Saved statistics summary to: {stats_file}")
    print("\nAnalysis complete!")


if __name__ == "__main__":
    analyze_results()
