import pandas as pd
from thefuzz import process
import os
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NutritionCalculator:
    """
    A class to calculate nutritional intake from food frequency questionnaire data.
    """
    
    def __init__(self, nutrition_data_path: str):
        """
        Initialize the calculator with nutrition reference data.
        
        Args:
            nutrition_data_path: Path to the Excel file containing nutrition reference data
        """
        self.nutrition_data_path = Path(nutrition_data_path)
        self.nutrition_df = None
        self.food_groups = []
        
        # Frequency multipliers for converting survey responses to weekly portions
        self.frequency_multipliers = {
            'freq_never': 0,
            'freq_month': 1/4,  # Once per month = 0.25 per week
            'freq_week': 1,     # Once per week
            'freq_2to4_week': 3,  # 2-4 times per week (average = 3)
            'freq_5to6_week': 5.5,  # 5-6 times per week (average = 5.5)
            'freq_daily': 7,    # Daily = 7 times per week
            'freq_multiple_daily': 14  # Multiple times daily (assuming 2x)
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
        # Rename unnamed columns to meaningful names based on the actual structure
        column_mappings = {
            'Unnamed: 1': 'food_item',  # This contains the food descriptions
            'Unnamed: 2': 'freq_never',
            'Unnamed: 3': 'freq_month', 
            'Unnamed: 4': 'freq_week',
            'Unnamed: 5': 'freq_2to4_week',
            'Unnamed: 6': 'freq_5to6_week',
            'Unnamed: 7': 'freq_daily',
            'Unnamed: 8': 'freq_multiple_daily',
            'Unnamed: 10': 'portion_small',
            'Unnamed: 11': 'portion_medium',
            'Unnamed: 12': 'portion_large'
        }
        
        survey_df = survey_df.rename(columns=column_mappings)
        
        # Filter out rows where food_item is NaN (these seem to be category headers)
        survey_df = survey_df[survey_df['food_item'].notna()].copy()
        
        # Get frequency columns
        freq_columns = [col for col in column_mappings.values() if col.startswith('freq_')]
        
        # Fill NaN values and convert to numeric
        survey_df[freq_columns] = survey_df[freq_columns].fillna('0')
        
        for col in freq_columns:
            # Replace 'x' with '1' and convert to float
            survey_df[col] = survey_df[col].astype(str).str.replace('x', '1')
            survey_df[col] = pd.to_numeric(survey_df[col], errors='coerce').fillna(0)
        
        logger.info(f"After cleaning: {len(survey_df)} valid food items")
        
        return survey_df
    
    def _calculate_weekly_portions(self, survey_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate weekly portions for each food item based on frequency responses.
        The frequency values encode portion size: 1=small, 2=medium, 3=large
        The portion columns contain the actual gram weights for each size.
        
        Args:
            survey_df: Cleaned survey dataframe
            
        Returns:
            Survey dataframe with calculated weekly portions and gram weights
        """
        # Clean portion columns - convert to numeric
        portion_columns = ['portion_small', 'portion_medium', 'portion_large']
        for col in portion_columns:
            if col in survey_df.columns:
                survey_df[col] = pd.to_numeric(survey_df[col], errors='coerce').fillna(0)
        
        survey_df['weekly_frequency'] = 0
        survey_df['portion_grams'] = 0
        
        # Process each frequency column
        for freq_col, time_multiplier in self.frequency_multipliers.items():
            if freq_col in survey_df.columns:
                freq_values = survey_df[freq_col]
                
                # For each row, check if there's a value in this frequency column
                for idx, freq_value in freq_values.items():
                    if freq_value > 0:  # If this frequency is selected
                        # Determine portion size based on the value (1, 2, or 3)
                        if freq_value == 1:  # Small portion
                            portion_weight = survey_df.loc[idx, 'portion_small']
                        elif freq_value == 2:  # Medium portion
                            portion_weight = survey_df.loc[idx, 'portion_medium']
                        elif freq_value == 3:  # Large portion
                            portion_weight = survey_df.loc[idx, 'portion_large']
                        else:
                            # Invalid value, default to medium
                            portion_weight = survey_df.loc[idx, 'portion_medium']
                        
                        # Calculate weekly frequency and store portion weight
                        survey_df.loc[idx, 'weekly_frequency'] += time_multiplier
                        survey_df.loc[idx, 'portion_grams'] = portion_weight
        
        # Calculate total weekly grams consumed
        survey_df['weekly_grams'] = survey_df['weekly_frequency'] * survey_df['portion_grams']

        return survey_df
    
    def _match_food_groups(self, survey_df: pd.DataFrame, min_score: int = 80) -> pd.DataFrame:
        """
        Match survey food items to nutrition database using fuzzy matching.
        
        Args:
            survey_df: Survey dataframe with food items
            min_score: Minimum matching score (0-100)
            
        Returns:
            Survey dataframe with matched food groups
        """
        def find_best_match(food_item: str) -> Optional[str]:
            if pd.isna(food_item):
                return None
            
            match, score = process.extractOne(food_item, self.food_groups)
            return match if score >= min_score else None
        
        survey_df['matched_food_group'] = survey_df['food_item'].apply(find_best_match)
        
        # Apply manual corrections
        survey_df['matched_food_group'] = survey_df.apply(
            lambda row: self.manual_corrections.get(row['food_item'], row['matched_food_group']),
            axis=1
        )
        
        # Log matching statistics
        total_items = len(survey_df)
        matched_items = survey_df['matched_food_group'].notna().sum()
        logger.info(f"Matched {matched_items}/{total_items} food items ({matched_items/total_items*100:.1f}%)")
        
        return survey_df
    
    def _calculate_total_nutrition(self, merged_df: pd.DataFrame) -> pd.Series:
        """
        Calculate total nutritional intake by multiplying weekly grams with nutritional values per 100g.
        
        Args:
            merged_df: Merged dataframe with survey and nutrition data
            
        Returns:
            Series with total nutritional values
        """
        # Get nutrient columns (exclude non-nutrient columns)
        exclude_cols = {'groupe_ffq', 'food_item', 'matched_food_group', 'weekly_frequency', 
                       'portion_grams', 'weekly_grams', 'portion_small', 'portion_medium', 'portion_large'}
        nutrient_columns = [col for col in self.nutrition_df.columns if col not in exclude_cols]
        
        # Calculate total nutrition for each nutrient
        total_nutrition = pd.Series(dtype=float)
        
        for nutrient in nutrient_columns:
            if nutrient in merged_df.columns:
                # Calculate intake: (weekly_grams / 100g) * nutrient_per_100g
                # This converts from per-100g values to actual consumption
                nutrient_intake = (merged_df['weekly_grams'] / 100.0 * 
                                 pd.to_numeric(merged_df[nutrient], errors='coerce')).fillna(0)
                total_nutrition[nutrient] = nutrient_intake.sum()
        
        return total_nutrition
    
    def calculate_nutrition(self, survey_path: str, output_dir: str) -> None:
        """
        Main method to calculate nutrition from survey data and save results.
        
        Args:
            survey_path: Path to the survey Excel file
            output_dir: Directory to save the results
        """
        try:
            survey_path = Path(survey_path)
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Processing survey: {survey_path.name}")
            
            # Load survey data (skip first 3 rows as they seem to be headers)
            survey_df = pd.read_excel(survey_path, header=3, dtype=str)
            logger.info(f"Loaded survey with {len(survey_df)} food items")
            
            # Debug: Print column names and first few rows
            logger.info(f"Survey columns: {list(survey_df.columns)}")
            logger.debug(f"First few rows:\n{survey_df.head()}")
            
            # Clean and process survey data
            survey_df = self._clean_survey_data(survey_df)
            survey_df = self._calculate_weekly_portions(survey_df)
            survey_df = self._match_food_groups(survey_df)
            
            # Merge with nutrition data
            merged_df = pd.merge(
                survey_df, 
                self.nutrition_df, 
                left_on='matched_food_group', 
                right_on='groupe_ffq', 
                how='left'
            )
            
            # Calculate total nutrition
            total_nutrition = self._calculate_total_nutrition(merged_df)
            
            # Save results
            output_filename = survey_path.stem + "_nutrition_summary.txt"
            output_path = output_dir / output_filename
            
            self._save_results(survey_path.name, total_nutrition, merged_df, output_path)
            
            logger.info(f"Successfully saved summary to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error processing {survey_path}: {e}")
            raise
    
    def _save_results(self, survey_filename: str, total_nutrition: pd.Series, 
                     merged_df: pd.DataFrame, output_path: Path) -> None:
        """
        Save calculation results to a text file.
        
        Args:
            survey_filename: Name of the survey file
            total_nutrition: Calculated total nutrition values
            merged_df: Merged dataframe for detailed breakdown
            output_path: Path to save the results
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"=== NUTRITIONAL INTAKE SUMMARY ===\n")
            f.write(f"Survey File: {survey_filename}\n")
            f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            
            f.write("TOTAL WEEKLY NUTRITIONAL INTAKE:\n")
            f.write("-" * 35 + "\n")
            for nutrient, value in total_nutrition.items():
                f.write(f"{nutrient}: {value:.2f}\n")


def main():
    """Main function to process all surveys in the surveys directory."""
    
    # Define paths
    script_dir = Path(__file__).parent
    nutrition_data_path = script_dir / ".." / ".." / "data" / "reference" / "nutrition_data.xlsx"
    surveys_dir = script_dir / ".." / ".." / "data" / "surveys"
    results_dir = script_dir / ".." / ".." / "data" / "results"
    
    try:
        # Initialize calculator
        calculator = NutritionCalculator(nutrition_data_path)
        
        # Process all survey files
        survey_files = list(surveys_dir.glob("*.xlsx"))
        
        if not survey_files:
            logger.warning(f"No Excel files found in {surveys_dir}")
            return
        
        logger.info(f"Found {len(survey_files)} survey files to process")
        
        for survey_file in survey_files:
            try:
                calculator.calculate_nutrition(survey_file, results_dir)
            except Exception as e:
                logger.error(f"Failed to process {survey_file.name}: {e}")
                continue
        
        logger.info("Processing complete!")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
