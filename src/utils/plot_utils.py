# File: src/utils/plot_utils.py
# Purpose: Data visualization and plotting utilities
# Target Lines: ≤150

"""
Methods to implement:
- compute_fft(data, sample_rate): Compute FFT of the input data
"""

import numpy as np
import logging


def compute_fft(data, sample_rate):
    """
    Compute the FFT (Fast Fourier Transform) of the input data.
    
    Args:
        data (list or numpy.ndarray): Time domain data
        sample_rate (float): Sample rate in Hz
        
    Returns:
        tuple: (frequencies, magnitudes)
            - frequencies (numpy.ndarray): Frequency values in Hz
            - magnitudes (numpy.ndarray): Magnitude values
    """
    try:
        # Convert to numpy array if not already
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        # Apply window function to reduce spectral leakage
        window = np.hanning(len(data))
        windowed_data = data * window
        
        # Compute FFT
        fft_result = np.fft.rfft(windowed_data)
        
        # Compute magnitude spectrum (absolute values)
        magnitudes = np.abs(fft_result)
        
        # Compute frequency values
        freq_step = sample_rate / len(data)
        frequencies = np.arange(len(magnitudes)) * freq_step
        
        return frequencies, magnitudes
        
    except Exception as e:
        logging.error(f"Error computing FFT: {str(e)}")
        # Return empty arrays on error
        return np.array([]), np.array([])


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement spectrogram computation
# def compute_spectrogram(data, sample_rate, window_size=256, overlap=0.5):
#     pass

# TODO: Implement data smoothing
# def smooth_data(data, window_size=5, method='moving_average'):
#     pass

# TODO: Implement peak detection
# def detect_peaks(data, threshold=0.5, min_distance=1):
#     pass

# How to extend and modify:
# 1. Add more transforms: Add wavelet transform, Hilbert transform, etc.
# 2. Add filtering functions: Add low-pass, high-pass, band-pass filters
# 3. Add statistical analysis: Add auto-correlation, cross-correlation functions