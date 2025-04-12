# File: src/utils/error_handler.py
# Purpose: Error handling and reporting utilities
# Target Lines: ≤150

"""
Methods to implement:
- handle_error(error, message): Handle an error with custom message
- log_error(error, logger): Log an error with the given logger
"""

import logging
import traceback
import sys


def handle_error(error, message=None, logger=None, raise_exception=False):
    """
    Handle an error with a custom message.
    
    Args:
        error (Exception): The exception object
        message (str, optional): Custom error message
        logger (logging.Logger, optional): Logger to use
        raise_exception (bool): Whether to re-raise the exception
        
    Returns:
        bool: False if error was handled, does not return if raise_exception is True
        
    Raises:
        Exception: Re-raises the original exception if raise_exception is True
    """
    # Get error details
    error_type = type(error).__name__
    error_message = str(error)
    stack_trace = traceback.format_exc()
    
    # Format the error message
    if message:
        formatted_message = f"{message}: {error_type} - {error_message}"
    else:
        formatted_message = f"{error_type}: {error_message}"
    
    # Log the error
    if logger:
        logger.error(formatted_message)
        logger.debug(stack_trace)
    else:
        logging.error(formatted_message)
        logging.debug(stack_trace)
    
    # Re-raise if requested
    if raise_exception:
        raise error
        
    return False


def log_error(error, logger=None):
    """
    Log an error with the given logger.
    
    Args:
        error (Exception): The exception object
        logger (logging.Logger, optional): Logger to use, uses root logger if None
        
    Returns:
        None
    """
    error_type = type(error).__name__
    error_message = str(error)
    stack_trace = traceback.format_exc()
    
    log = logger if logger else logging.getLogger()
    
    log.error(f"{error_type}: {error_message}")
    log.debug(stack_trace)


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement error notification function
# def notify_error(error, notification_method='email', recipients=None):
#     pass

# TODO: Implement retry mechanism
# def retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
#     pass

# TODO: Implement error summary reporting
# def generate_error_report(errors_list, include_stacktrace=True):
#     pass

# How to extend and modify:
# 1. Add email notification: Add functionality to email error reports
# 2. Add error categorization: Categorize errors by severity and type
# 3. Add retry mechanism: Add a decorator to retry failed operations