import os
import numpy as np
import pandas as pd
from dataclasses import dataclass
import json

@dataclass
class PCPSConfig:
    """Configuration parameters for PCPS algorithm"""
    window_size: int = 20        # Number of samples in the processing window
    max_threshold: float = 0.5    # Threshold for fear detection
    min_pupil_size: float = 0.8   # Minimum physiologically plausible pupil size (mm)
    max_pupil_size: float = 10.0  # Maximum physiologically plausible pupil size (mm)
    polynomial_degree: int = 3    # Degree of polynomial for luminance fitting

class PCPS:
    def __init__(self, config: PCPSConfig | None = None):
        """Initialize the PCPS algorithm processor."""
        self.config = config or PCPSConfig()
        self.coeffs: np.ndarray | None = None
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters"""
        if self.config.window_size < 5:  # Reduced minimum window size
            self.config.window_size = 5
            print(f"Warning: Window size too small, using {self.config.window_size}")
        if not (0 < self.config.max_threshold < 1000):
            raise ValueError("Threshold must be between 0 and 1000")
        if self.config.polynomial_degree < 1:
            raise ValueError("Polynomial degree must be at least 1")

    def preprocess_pupil(self, y: np.ndarray) -> np.ndarray:
        """Clean and preprocess pupil diameter data."""
        y_processed = y.copy().astype(np.float64)
        y_processed[~np.isfinite(y_processed)] = np.nan
        
        # Remove physiologically implausible values
        mask = (y_processed < self.config.min_pupil_size) | (y_processed > self.config.max_pupil_size)
        y_processed[mask] = np.nan
        
        # Linear interpolation for missing values
        if np.isnan(y_processed).any():
            nans = np.isnan(y_processed)
            y_processed[nans] = np.interp(
                np.flatnonzero(nans),
                np.flatnonzero(~nans),
                y_processed[~nans]
            )
        
        return y_processed

    def calculate_fear_timeline(self, pupil: np.ndarray, luminances: np.ndarray) -> dict:
        """Calculate fear index with per-sample values."""
        if len(pupil) != len(luminances):
            raise ValueError("Pupil and luminance arrays must be the same length")
        
        # Process data
        cleaned_pupil = self.preprocess_pupil(pupil)
        
        # Simple baseline removal
        baseline = np.mean(cleaned_pupil)
        processed = cleaned_pupil - baseline
        
        # Calculate power for each point
        power = processed ** 2
        
        # Calculate rolling statistics
        window = min(self.config.window_size, len(power))
        if window < 5:  # Minimum window size
            window = len(power)
            
        mean_power = pd.Series(power).rolling(window=window, min_periods=1, center=True).mean().values
        std_power = pd.Series(power).rolling(window=window, min_periods=1, center=True).std().values
        
        # Calculate z-scores
        with np.errstate(divide='ignore', invalid='ignore'):
            z_scores = np.where(std_power > 0, (power - mean_power) / std_power, 0)
        
        # Calculate fear levels (0-1 scale)
        fear_levels = 1 / (1 + np.exp(-z_scores))  # Sigmoid to keep between 0-1
        
        # Calculate summary statistics
        max_power = np.max(power)
        avg_mean_power = np.mean(mean_power)
        avg_std_power = np.mean(std_power)
        
        return {
            'summary': {
                'fear_index': float(max_power),
                'mean_power': float(avg_mean_power),
                'std_power': float(avg_std_power),
                'max_fear': float(np.max(fear_levels)),
                'avg_fear': float(np.mean(fear_levels)),
                'samples_processed': len(pupil)
            },
            'timeline': [
                {
                    'timestamp': i,
                    'pupil_size': float(pupil[i]),
                    'luminance': float(luminances[i]),
                    'fear_level': float(fear_levels[i]),
                    'z_score': float(z_scores[i])
                }
                for i in range(len(pupil))
            ]
        }

class FearIndexProcessor:
    def __init__(self, config: PCPSConfig | None = None):
        self.pcps = PCPS(config)
    
    def process_file(self, file_path: str) -> dict:
        """Process a single CSV file and return results with timeline data."""
        try:
            # Read and validate data
            df = pd.read_csv(file_path)
            print(f"Processing {len(df)} samples from {file_path}")
            
            # Calculate fear metrics with timeline
            results = self.pcps.calculate_fear_timeline(
                pupil=df['average_pupil_diameter_mm'].values,
                luminances=df['screen_brightness'].values
            )
            
            # Add metadata
            results['file'] = os.path.basename(file_path)
            results['timestamp'] = pd.Timestamp.now().isoformat()
            
            return results
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error processing {file_path}: {error_msg}")
            return {
                'error': error_msg,
                'file': os.path.basename(file_path),
                'success': False
            }

def main():
    """Command-line interface for fear index processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate fear index from pupil data.')
    parser.add_argument('input_file', help='Path to input CSV file')
    parser.add_argument('--threshold', type=float, default=0.5, 
                       help='Fear detection threshold (default: 0.5)')
    parser.add_argument('--output', '-o', help='Output JSON file path (default: input_file + _results.json)')
    
    args = parser.parse_args()
    
    try:
        config = PCPSConfig(max_threshold=args.threshold)
        processor = FearIndexProcessor(config)
        results = processor.process_file(args.input_file)
        
        # Determine output file path
        if not args.output:
            base_name = os.path.splitext(args.input_file)[0]
            output_path = f"{base_name}_results.json"
        else:
            output_path = args.output
        
        # Save results to file
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {os.path.abspath(output_path)}")
        print("\nSummary:")
        print(json.dumps(results.get('summary', {}), indent=2))
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())