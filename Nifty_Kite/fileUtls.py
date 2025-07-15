import os
import pickle
from datetime import datetime
import pandas as pd
import traceback


def add_line_to_file(file_path, line):
    try:
        with open(file_path, 'a') as file:
            file.write(line + '\n')  # Append a newline character to the end of the line
            file_name = os.path.basename(file_path)
        print(f"{file_name}: {line}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(traceback.format_exc())


def add_line_break_to_last_line(file_path):
    try:
        with open(file_path, 'r+') as file:
            lines = file.readlines()
            if lines:
                last_line = lines[-1]
                if not last_line.endswith('\n'):
                    last_line += '\n'
                    lines[-1] = last_line
                    file.seek(0)
                    file.writelines(lines)
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        print(traceback.format_exc())
    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())


def is_file_empty(file_path):
    try:
        if os.path.exists(file_path):
            return os.stat(file_path).st_size == 0
        else:
            return True  # File does not exist
    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
        return False


def write_to_pickle_file(file_path, data):
    try:
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
        print(f"Data successfully written to {file_path}")
    except Exception as e:
        print(f"An error occurred while writing the file: {str(e)}")
        print(traceback.format_exc())


def read_from_pickle_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            data = pickle.load(file)
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        print(traceback.format_exc())
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {str(e)}")
        print(traceback.format_exc())
        return None


def is_file_created_or_modified_today(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        return False

    # Get the file's modification timestamp //alternate os.path.getmtime
    file_stats = os.stat(file_path)
    modification_time = datetime.fromtimestamp(file_stats.st_mtime)

    # Get today's date
    today = datetime.now()

    # Compare the modification date with today's date
    if modification_time.date() == today.date():
        return True
    else:
        return False


def getLogStr_from_dfRow(row, log_format: list):
    try:
        log_str = ""
        for i in range(0, log_format.__len__() - 1):
            log_str = log_str + str(row[log_format[i]]) + ","
        log_str = log_str + str(row[log_format[log_format.__len__() - 1]])
        return log_str
    except Exception as e:
        print(f"An error occurred while getting Log String from Dataframe: {str(e)}")
        print(traceback.format_exc())
        return ""
