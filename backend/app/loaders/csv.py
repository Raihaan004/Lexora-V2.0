import pandas as pd
from pathlib import Path
from app.loaders.base import BaseLoader

class CSVLoader(BaseLoader):
    """Parses CSV sheets offline using pandas and structures rows as descriptive text strings."""

    def load(self, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found at: {file_path}")
            
        try:
            # Load CSV using pandas
            df = pd.read_csv(file_path)
            if df.empty:
                return ""
                
            row_records = []
            columns = df.columns.tolist()
            
            for idx, row in df.iterrows():
                row_items = []
                for col in columns:
                    val = row[col]
                    # Filter out NaN/empty entries to optimize size
                    if pd.notna(val) and str(val).strip() != "":
                        row_items.append(f"{col}: {str(val).strip()}")
                        
                if row_items:
                    row_records.append(f"Row {idx + 1}: " + ", ".join(row_items))
                    
            return "\n".join(row_records)
            
        except Exception as e:
            raise RuntimeError(f"Error reading CSV '{file_path.name}': {str(e)}")
