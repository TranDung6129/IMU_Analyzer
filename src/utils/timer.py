# File: src/utils/timer.py
# Purpose: Timer utilities for benchmarking and performance monitoring
# Target Lines: ≤150

"""
Methods to implement:
- benchmark(name): Context manager for timing code blocks
"""

import time
import logging
from contextlib import contextmanager


@contextmanager
def benchmark(name, logger=None):
    """
    Context manager for benchmarking code execution time.
    
    Args:
        name (str): Name of the operation being benchmarked
        logger (logging.Logger, optional): Logger to use, if None uses print
        
    Yields:
        None
        
    Example:
        with benchmark("Database query"):
            results = db.execute_query()
    """
    start_time = time.time()
    
    try:
        yield
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        message = f"[BENCHMARK] {name} completed in {elapsed_time:.4f} seconds"
        
        if logger:
            logger.info(message)
        else:
            print(message)

# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement execution_time decorator
# @execution_time
# def function_to_measure():
#     pass

# TODO: Implement Timer class with start/stop methods
# class Timer:
#     def start(self):
#         pass
#     def stop(self):
#         pass
#     def reset(self):
#         pass

# How to extend and modify:
# 1. Add more statistics: Modify benchmark to track min/max/avg times
# 2. Add async support: Create an async version of benchmark
# 3. Add memory tracking: Add memory usage tracking to benchmark