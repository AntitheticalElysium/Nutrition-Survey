# Nutrition Survey Analysis Tool

A user-friendly tool for analyzing Food Frequency Questionnaire (FFQ) data and calculating nutritional intake from survey responses.

## 📋 What This Tool Does

This tool takes your food survey data (Excel files) and:
- ✅ Calculates **daily** nutritional intake for each participant
- ✅ Matches food items from surveys to a nutritional database
- ✅ Generates easy-to-read summary reports in Excel format, comparing individual intake to reference values.

## 📁 Project Structure

```
NutritionSurvey/
├── data/
│   ├── surveys/          ← Put your survey Excel files here
│   ├── reference/        ← Contains nutrition_data.xlsx, ref_man.xlsx, ref_woman.xlsx
│   └── results/          ← Generated summaries appear here
├── src/
│   ├── calculator/       ← Main calculation script
│   └── analysis/         ← (Future: Analysis and plotting script)
└── reports/
    └── figures/          ← (Future: Generated charts and statistics)
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
   - The tool expects data starting from row 1 (row 1 is the header).
   - **Sex Information**: The participant's sex ('M' or 'F') must be specified in cell `K2` of the survey file.

2. **Nutrition Database**: Ensure `nutrition_data.xlsx` is in `data/reference/`
   - This contains the nutritional values for different food groups.

3. **Reference Files**: Ensure `ref_man.xlsx` and `ref_woman.xlsx` are in `data/reference/`
   - These files contain reference nutritional values for men and women, respectively.

### Step 2: Run the Nutrition Calculator

Open Terminal, navigate to your project folder, and run:

```bash
cd src/calculator
python3 calculate.py
```

**What happens:**
- The tool processes all `.xlsx` files in `data/surveys/`
- For each survey, it calculates **daily** nutritional intake.
- Food items appearing multiple times in the survey are aggregated (their daily consumption is summed).
- Results are saved as Excel files (`.xlsx`) in `data/results/`, comparing the calculated intake to the appropriate sex-specific reference values.

**Example output you'll see (in the generated Excel file):**
```
                                 Nutriments  Valeurs ref Homme  Valeurs obtenues  Difference (%)
0                            Protéines    g               50.0         40.456714      -19.086571
1                              Glucides   g              260.0       1362.983000      424.224231
2                                 Sucres  g               90.0       1072.042607     1091.158452
...
```

## 📈 Understanding Your Results

### Individual Survey Summaries
Each survey generates an Excel file like `survey_1_nutrition_summary.xlsx` in `data/results/`.

**Key columns in the output:**
- **Nutriments**: The name of the nutrient.
- **Valeurs ref Homme/Femme**: The reference daily intake value for the corresponding sex.
- **Valeurs obtenues**: The calculated daily intake value for the survey participant.
- **Difference (%)**: The percentage difference between the calculated intake and the reference value.

**How calculations work:**
The tool calculates nutrition based on actual portion sizes and frequencies:
1. Takes the frequency (how often you eat the food) and portion size (from your survey).
2. Calculates total daily grams consumed for each food item.
3. Aggregates daily grams for duplicate food items.
4. Uses nutrition database (values per 100g) to calculate actual daily nutrient intake.
5. Compares calculated intake to reference values and computes the percentage difference.

**Example calculation (conceptual):**
- Food: Bread, eaten daily (1×/day) with medium portion (100g)
- Daily consumption: 1 × 100g = 100g per day
- If bread contains 5g protein per 100g: (100g ÷ 100g) × 5g = 5g protein per day

## 📝 Survey Data Format

Your Excel survey files should have this structure (header in row 1):

| Column | Header (Row 1) | Content | Example |
|--------|----------------|---------|---------|
| A      | `ALIMENT`      | Food items | "Pains blancs" |
| B      | `JAMAIS`       | Frequency: Never | (empty or 0) |
| C      | `1-3 MOIS`     | Frequency: 1-3 times per month | 1, 2, or 3 (portion size selection) |
| D      | `1 SEMAINE`    | Frequency: 1 time per week | 1, 2, or 3 |
| E      | `2-4 SEMAINE`  | Frequency: 2-4 times per week | 1, 2, or 3 |
| F      | `5-6 SEMAINES` | Frequency: 5-6 times per week | 1, 2, or 3 |
| G      | `TOUS`         | Frequency: Daily | 1, 2, or 3 |
| H      | `PETITE `      | Small portion size (grams) | "100" |
| I      | `MOYENNE `     | Medium portion size (grams) | "150" |
| J      | `GROSSE`       | Large portion size (grams) | "200" |
| K      | `SEXE`         | Participant's sex (only in K2) | "M" or "F" |

**How the portion system works:**
- **Frequency columns (C-G)** contain values 1, 2, or 3:
  - **1** = Small portion (uses column H value)
  - **2** = Medium portion (uses column I value)  
  - **3** = Large portion (uses column J value)
- **Portion columns (H-J)** contain the actual gram weights.

**Example:**
If someone puts "2" in the "1 SEMAINE" frequency column for bread:
- This means: "I eat bread once per week with a medium portion"
- The tool will use the medium portion weight from column I.
- If medium portion = 150g, total weekly intake = 1 × 150g = 150g per week. This is then converted to daily.

**Important:** Only one frequency column should have a value per food item row. Food items can appear multiple times in the survey, and their daily consumption will be summed.

## 🔍 Troubleshooting

### Common Issues:

**"No survey files found"**
- Check that your Excel files are in `data/surveys/`
- Ensure files have `.xlsx` extension

**"Nutrition data file not found"**
- Verify `nutrition_data.xlsx` is in `data/reference/`
- Check file name spelling exactly

**"Column 'Valeurs obtenues' not found in the reference file."**
- Ensure `ref_man.xlsx` and `ref_woman.xlsx` are in `data/reference/` and contain the expected column headers.

**"Sex not specified or invalid in cell K2."**
- Ensure cell `K2` in your survey file contains either 'M' or 'F' (case-insensitive).

**"Low matching percentage"**
- This is normal - some food items might not match the database.
- The tool will still calculate nutrition for matched items.
- Unmatched items are effectively ignored in the calculation.

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