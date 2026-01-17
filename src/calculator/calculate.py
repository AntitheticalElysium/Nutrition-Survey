import pandas as pd
from thefuzz import process
import logging
from pathlib import Path
import shutil
import openpyxl
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NutritionCalculator:
    """
    A class to calculate nutritional intake from food frequency questionnaire data.
    """
    
    def __init__(self, nutrition_data_path: str, ref_man_path: str, ref_woman_path: str):
        """
        Initialize the calculator with nutrition reference data.
        
        Args:
            nutrition_data_path: Path to the Excel file containing nutrition reference data
        """
        self.nutrition_data_path = Path(nutrition_data_path)
        self.ref_man_path = Path(ref_man_path)
        self.ref_woman_path = Path(ref_woman_path)
        self.nutrition_df = None
        self.food_groups = []
        
        # Frequency multipliers for converting survey responses to daily portions
        self.frequency_multipliers = {
            'JAMAIS': 0,
            '1-3 MOIS': (2/30.5),
            '1 SEMAINE': 1/7,
            '2-4 SEMAINE': 3/7,
            '5-6 SEMAINES': 5.5/7,
            'TOUS': 1,
            # Additional column names from survey_2.xlsx
            'JAMAIS ': 0,
            '1-3 FOIS MOIS': (2/30.5),
            '1 FOIS SEMAINE': 1/7,
            '2/4 FOIS SEMAINE': 3/7,
            '5/6 FOIS SEMAINE': 5.5/7,
            'TOUS LES JOURS': 1,
        }
        
        # Manual corrections for food matching
        self.manual_corrections = {
            "Viande de porc (hors charcuterie): rôti, émincés, côte, filet mignon": 
            "Viande de porc : rôti, émincés, côte, filet mignon"
        }
        
        self._load_nutrition_data()
    
    def _load_nutrition_data(self) -> None:
        """Load and prepare nutrition reference data."""
        try:
            self.nutrition_df = pd.read_excel(self.nutrition_data_path)
            self.food_groups = self.nutrition_df['groupe_ffq'].tolist()
            logger.info(f"Loaded nutrition data with {len(self.nutrition_df)} food groups")
        except FileNotFoundError:
            raise FileNotFoundError(f"Nutrition data file not found: {self.nutrition_data_path}")
        except Exception as e:
            raise Exception(f"Error loading nutrition data: {e}")
    
    def _clean_survey_data(self, survey_df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and prepare survey data for processing.
        
        Args:
            survey_df: Raw survey dataframe
            
        Returns:
            Cleaned survey dataframe
        """
        # Clean column names by stripping whitespace
        survey_df.columns = survey_df.columns.str.strip()

        column_mappings = {
            'ALIMENT': 'food_item',
            'PETITE': 'portion_small',
            'MOYENNE': 'portion_medium',
            'GROSSE': 'portion_large'
        }
        
        survey_df = survey_df.rename(columns=column_mappings)
        survey_df = survey_df[survey_df['food_item'].notna()].copy()
        
        # Get frequency columns from the keys of frequency_multipliers
        freq_columns = [col for col in self.frequency_multipliers.keys() if col in survey_df.columns]
        
        survey_df[freq_columns] = survey_df[freq_columns].fillna('0')
        
        for col in freq_columns:
            survey_df[col] = survey_df[col].astype(str).str.replace('x', '1')
            survey_df[col] = pd.to_numeric(survey_df[col], errors='coerce').fillna(0)
        
        logger.info(f"After cleaning: {len(survey_df)} valid food items")
        return survey_df
    
    def _calculate_daily_portions(self, survey_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily portions for each food item based on frequency responses.
        """
        portion_columns = ['portion_small', 'portion_medium', 'portion_large']
        for col in portion_columns:
            if col in survey_df.columns:
                survey_df[col] = pd.to_numeric(survey_df[col], errors='coerce').fillna(0)
        
        survey_df['daily_frequency'] = 0.0
        survey_df['portion_grams'] = 0
        
        # Iterate through the actual frequency columns in the DataFrame
        for freq_col_name, time_multiplier in self.frequency_multipliers.items():
            if freq_col_name in survey_df.columns:
                freq_values = survey_df[freq_col_name]
                for idx, freq_value in freq_values.items():
                    if freq_value > 0:  # If this frequency is selected
                        # Determine portion size based on the value (1, 2, or 3)
                        if freq_value == 1:
                            portion_weight = survey_df.loc[idx, 'portion_small']
                        elif freq_value == 2:
                            portion_weight = survey_df.loc[idx, 'portion_medium']
                        elif freq_value == 3:
                            portion_weight = survey_df.loc[idx, 'portion_large']
                        else:
                            portion_weight = survey_df.loc[idx, 'portion_medium']
                        
                        survey_df.loc[idx, 'daily_frequency'] += time_multiplier
                        survey_df.loc[idx, 'portion_grams'] = portion_weight
        
        survey_df['daily_grams'] = survey_df['daily_frequency'] * survey_df['portion_grams']
        return survey_df
    
    def _match_food_groups(self, survey_df: pd.DataFrame, min_score: int = 80) -> pd.DataFrame:
        """
        Match survey food items to nutrition database using fuzzy matching.
        
        Args:
            survey_df: Survey dataframe with food items (after aggregation)
            min_score: Minimum matching score (0-100)
            
        Returns:
            Survey dataframe with matched food groups
        """
        def find_best_match(food_item: str):
            if pd.isna(food_item):
                return None
            match, score = process.extractOne(food_item, self.food_groups)
            return match if score >= min_score else None
        
        survey_df['matched_food_group'] = survey_df['food_item'].apply(find_best_match)
        
        # Apply manual corrections - ensure 'food_item' is the only column accessed here
        survey_df['matched_food_group'] = survey_df.apply(
            lambda row: self.manual_corrections.get(row['food_item'], row['matched_food_group']),
            axis=1
        )
        
        total_items = len(survey_df)
        matched_items = survey_df['matched_food_group'].notna().sum()
        logger.info(f"Matched {matched_items}/{total_items} food items ({matched_items/total_items*100:.1f}%)")
        
        return survey_df
    
    def _calculate_total_nutrition(self, merged_df: pd.DataFrame) -> pd.Series:
        """
        Calculate total nutritional intake by multiplying daily grams with nutritional values per 100g.
        """
        exclude_cols = {'groupe_ffq', 'food_item', 'matched_food_group', 'daily_frequency', 
                       'portion_grams', 'portion_small', 'portion_medium', 'portion_large'}
        nutrient_columns = [col for col in self.nutrition_df.columns if col not in exclude_cols]
        total_nutrition = pd.Series(dtype=float)
        
        for nutrient in nutrient_columns:
            if nutrient in merged_df.columns:
                nutrient_intake = (merged_df['daily_grams'] / 100.0 * 
                                 pd.to_numeric(merged_df[nutrient], errors='coerce')).fillna(0)
                total_nutrition[nutrient] = nutrient_intake.sum()
        
        return total_nutrition
    
    def calculate_nutrition(self, survey_path: str, output_dir: str) -> None:
        """
        Main method to calculate nutrition from survey data and save results.
        """
        try:
            survey_path = Path(survey_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Processing survey: {survey_path.name}")

            # Read sex from cell K2
            workbook = openpyxl.load_workbook(survey_path)
            sheet = workbook.active
            sex = sheet['K2'].value # Assuming K2 contains the sex
            if not sex or sex.upper() not in ['M', 'F']:
                raise ValueError("Sex not specified or invalid in cell K2. Should be 'M' or 'F'.")
            sex = sex.upper()

            survey_df = pd.read_excel(survey_path, header=0, dtype=str) # Changed header to 0
            logger.info(f"Loaded survey with {len(survey_df)} food items")
            
            survey_df = self._clean_survey_data(survey_df)
            survey_df = self._calculate_daily_portions(survey_df)

            # Aggregate duplicate food items by summing their daily_grams
            # Ensure 'food_item' is the index for groupby if it's not already
            survey_df = survey_df.groupby('food_item', as_index=False)['daily_grams'].sum()
            
            survey_df = self._match_food_groups(survey_df)
            
            merged_df = pd.merge(
                survey_df, 
                self.nutrition_df, 
                left_on='matched_food_group', 
                right_on='groupe_ffq', 
                how='left'
            )
            
            total_nutrition = self._calculate_total_nutrition(merged_df)
            
            output_filename = survey_path.stem + "_nutrition_summary.xlsx"
            output_path = output_dir / output_filename
            
            self._save_results(sex, survey_path.name, total_nutrition, output_path)
            
            logger.info(f"Successfully saved summary to: {output_path}")
            return sex, total_nutrition
            
        except Exception as e:
            logger.error(f"Error processing {survey_path}: {e}")
            raise
    
    def _save_results(self, sex: str, survey_filename: str, total_nutrition: pd.Series, output_path: Path) -> None:
        """
        Save calculation results to an Excel file, comparing with reference values.
        """
        ref_path = self.ref_man_path if sex == 'M' else self.ref_woman_path
        shutil.copy(ref_path, output_path)

        df = pd.read_excel(output_path, header=0) # Changed header to 0
        df.columns = df.columns.str.strip()

        val_obtenues_col = None
        for col in df.columns:
            if "Valeurs obtenues" in str(col):
                val_obtenues_col = col
                break
        
        if not val_obtenues_col:
            raise ValueError("Column 'Valeurs obtenues' not found in the reference file.")

        nutrient_col = df.columns[0]
        ref_col = df.columns[1]

        df[ref_col] = df[ref_col].astype(str).str.extract(r'(\d+\.?\d*)').astype(float)
        df[val_obtenues_col] = pd.to_numeric(df[val_obtenues_col], errors='coerce')

        nutrient_mapping = {
            "protéines": "proteines",
            "glucides": "glucides",
            "lipides": "lipides",
            "sucres": "sucres",
            "fibres": "fibres",
            "ag saturés": "ags",
            "matières grasses": "lipides",
            "sel": "sel",
            "vitamine a": "retinol",
            "vitamine b1": "vitamine_b1",
            "vitamine b2": "vitamine_b2",
            "vitamine b3": "vitamine_b3",
            "vitamine b5": "vitamine_b5",
            "vitamine b6": "vitamine_b6",
            "vitamine b9": "vitamine_b9",
            "vitamine b12": "vitamine_b12",
            "vitamine c": "vitamine_c",
            "vitamine d": "vitamine_d",
            "vitamine e": "vitamine_e",
            "vitamine k": "vitamine_k2",
            "calcium": "calcium",
            "cuivre": "cuivre",
            "fer": "fer",
            "iode": "iode",
            "magnesium": "magnesium",
            "phosphore": "phosphore",
            "potassium": "potassium",
            "selenium": "selenium",
            "sodium": "sodium",
            "zinc": "zinc"
        }

        for idx, row in df.iterrows():
            nutrient_name_full = str(row[nutrient_col]).lower()
            for key, val in nutrient_mapping.items():
                if key in nutrient_name_full:
                    if val in total_nutrition:
                        df.loc[idx, val_obtenues_col] = total_nutrition[val]
                        break
        
        df[val_obtenues_col] = df[val_obtenues_col].fillna(0)

        df['Difference (%)'] = (((df[val_obtenues_col] - df[ref_col]) / df[ref_col]) * 100).round(1)
        df['Difference (%)'] = df['Difference (%)'].fillna(0)

        df.to_excel(output_path, index=False)
    
    def _save_statistics(self, results_by_sex: dict, output_dir: Path) -> None:
        """
        Save aggregate statistics (mean, median, std, min, max) for each nutrient by sex.
        Creates a user-friendly Excel file with French labels.
        """
        output_path = output_dir / "statistiques_nutritionnelles.xlsx"
        
        # French labels for statistics
        stat_labels = {
            'mean': 'Moyenne',
            'median': 'Médiane', 
            'std': 'Écart-type',
            'min': 'Minimum',
            'max': 'Maximum',
            'count': 'Nombre de participants'
        }
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sex, label in [('M', 'Statistiques Hommes'), ('F', 'Statistiques Femmes')]:
                if not results_by_sex.get(sex):
                    continue
                
                # Combine all results for this sex into a DataFrame
                df = pd.DataFrame(results_by_sex[sex])
                
                # Calculate statistics
                stats = pd.DataFrame({
                    stat_labels['mean']: df.mean().round(2),
                    stat_labels['median']: df.median().round(2),
                    stat_labels['std']: df.std().round(2),
                    stat_labels['min']: df.min().round(2),
                    stat_labels['max']: df.max().round(2),
                    stat_labels['count']: len(df)
                })
                
                # Reset index to make nutrient names a column
                stats = stats.reset_index()
                stats = stats.rename(columns={'index': 'Nutriment'})
                
                stats.to_excel(writer, sheet_name=label, index=False)
        
        logger.info(f"Statistiques sauvegardées dans: {output_path}")

def main():
    """Main function to process all surveys in the surveys directory."""
    
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent
    nutrition_data_path = base_dir / "data" / "reference" / "nutrition_data.xlsx"
    ref_man_path = base_dir / "data" / "reference" / "ref_man.xlsx"
    ref_woman_path = base_dir / "data" / "reference" / "ref_woman.xlsx"
    surveys_dir = base_dir / "data" / "surveys"
    results_dir = base_dir / "data" / "results"
    
    try:
        calculator = NutritionCalculator(nutrition_data_path, ref_man_path, ref_woman_path)
        
        survey_files = list(surveys_dir.glob("*.xlsx"))
        
        if not survey_files:
            logger.warning(f"No Excel files found in {surveys_dir}")
            return
        
        logger.info(f"Found {len(survey_files)} survey files to process")
        
        # Collect results by sex for aggregate statistics
        results_by_sex = {'M': [], 'F': []}
        
        for survey_file in survey_files:
            if survey_file.name.startswith('~'):
                continue
            try:
                result = calculator.calculate_nutrition(survey_file, results_dir)
                if result:
                    sex, nutrition = result
                    results_by_sex[sex].append(nutrition)
            except Exception as e:
                logger.error(f"Failed to process {survey_file.name}: {e}")
                continue
        
        # Generate aggregate statistics if we have results
        if results_by_sex['M'] or results_by_sex['F']:
            calculator._save_statistics(results_by_sex, results_dir)
        
        logger.info("Processing complete!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()