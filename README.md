# Nutrition Survey Analysis Tool

A user-friendly tool for analyzing Food Frequency Questionnaire (FFQ) data and calculating nutritional intake from survey responses.

## 📋 What This Tool Does

This tool takes your food survey data (Excel files) and:
- ✅ Calculates weekly nutritional intake for each participant
- ✅ Matches food items from surveys to a nutritional database
- ✅ Generates easy-to-read summary reports
- ✅ Creates visual charts and statistics for analysis

## 📁 Project Structure

```
NutritionSurvey/
├── data/
│   ├── surveys/          ← Put your survey Excel files here
│   ├── reference/        ← Contains nutrition_data.xlsx
│   └── results/          ← Generated summaries appear here
├── src/
│   ├── calculator/       ← Main calculation script
│   └── analysis/         ← Analysis and plotting script
└── reports/
    └── figures/          ← Generated charts and statistics
```

## 🔧 Installation & Setup

### Prerequisites
You need Python 3.7 or newer installed on your computer.

#### **For Mac Users:**
```bash
# Install Python using Homebrew (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python

# Or download from python.org if you prefer
```

#### **For Linux Users:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip
```

### Install Required Packages

Open Terminal and navigate to your project folder, then run:

```bash
pip3 install -r requirements.txt
```

This will automatically install all the necessary packages listed in the `requirements.txt` file.

## 📊 How to Use

### Step 1: Prepare Your Data

1. **Survey Files**: Place your survey Excel files in the `data/surveys/` folder
   - Files should be named like: `survey_1.xlsx`, `survey_2.xlsx`, etc.
   - The tool expects data starting from row 4 (rows 1-3 are headers)

2. **Nutrition Database**: Ensure `nutrition_data.xlsx` is in `data/reference/`
   - This contains the nutritional values for different food groups

### Step 2: Run the Nutrition Calculator

Open Terminal, navigate to your project folder, and run:

```bash
cd src/calculator
python3 calculate.py
```

**What happens:**
- The tool processes all `.xlsx` files in `data/surveys/`
- For each survey, it calculates weekly nutritional intake
- Results are saved as text files in `data/results/`

**Example output you'll see:**
```
2025-08-01 06:39:43 - INFO - Loaded nutrition data with 135 food groups
2025-08-01 06:39:43 - INFO - Found 2 survey files to process
2025-08-01 06:39:43 - INFO - Processing survey: survey_1.xlsx
2025-08-01 06:39:43 - INFO - After cleaning: 145 valid food items
2025-08-01 06:39:43 - INFO - Matched 98/145 food items (67.6%)
2025-08-01 06:39:43 - INFO - Successfully saved summary to: ../../data/results/survey_1_nutrition_summary.txt
```

### Step 3: Generate Analysis & Charts

```bash
cd ../analysis
python3 analyze.py
```

**What happens:**
- Reads all nutrition summary files
- Creates comparison charts between surveys
- Generates statistical summaries
- Saves everything in `reports/figures/`

## 📈 Understanding Your Results

### Individual Survey Summaries
Each survey generates a file like `survey_1_nutrition_summary.txt`:

```
=== NUTRITIONAL INTAKE SUMMARY ===
Survey File: survey_1.xlsx
Analysis Date: 2025-08-01 06:39:44
==================================================
TOTAL WEEKLY NUTRITIONAL INTAKE:
-----------------------------------
proteines: 245.67
lipides: 189.23
glucides: 567.89
fibres: 23.45
calcium: 890.12
fer: 12.34
vitamine_c: 78.90
...
```

**What this means:**
- **proteines**: Total protein intake per week (grams)
- **lipides**: Total fat intake per week (grams)  
- **glucides**: Total carbohydrate intake per week (grams)
- **fibres**: Total fiber intake per week (grams)
- **calcium**: Total calcium intake per week (milligrams)
- **fer**: Total iron intake per week (milligrams)
- **vitamine_c**: Total vitamin C intake per week (milligrams)

### Analysis Charts & Statistics

After running the analysis, you'll find in `reports/figures/`:

1. **`average_nutritional_intake.png`**: Bar chart showing average intake across all surveys
2. **`survey_comparison.png`**: Comparison chart between different surveys (if multiple)
3. **`nutritional_statistics.txt`**: Detailed statistics with averages and variations

## 📝 Survey Data Format

Your Excel survey files should have this structure:

| Column | Content | Example |
|--------|---------|---------|
| A | Food categories | "Item : viande, œuf, poisson" |
| B | Food items | "Viande rouge: bœuf, veau, agneau" |
| C-I | Frequency responses | "x" or blank for each frequency option |
| J-L | Portion sizes | Numbers like "80", "130", "200" |

**Frequency columns represent:**
- C: Never
- D: Monthly  
- E: Weekly
- F: 2-4 times per week
- G: 5-6 times per week
- H: Daily
- I: Multiple times daily

## 🔍 Troubleshooting

### Common Issues:

**"No survey files found"**
- Check that your Excel files are in `data/surveys/`
- Ensure files have `.xlsx` extension

**"Nutrition data file not found"**
- Verify `nutrition_data.xlsx` is in `data/reference/`
- Check file name spelling exactly

**"Low matching percentage"**
- This is normal - some food items might not match the database
- The tool will still calculate nutrition for matched items
- Unmatched items are listed in the summary for manual review

**"Module not found" errors**
- Run the pip install command again:
  ```bash
  pip3 install -r requirements.txt
  ```

### Getting Help:

If you encounter issues:
1. Check that all required packages are installed
2. Verify your file structure matches the expected layout
3. Look at the error messages - they usually indicate what's wrong
4. Check that your survey files match the expected format
