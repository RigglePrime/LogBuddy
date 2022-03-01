# LogBuddy

LogBuddy is a helper tool for reading log files. It has features to:
- combine multiple log files
- sort them however you want
- filter out logs by who performed the action, where it happened
- filter out logs that a person couldn't have heard or seen
- work with multiple filters (filter the filtered output)
- write the resulting set to a file

## Running

To run:

- `pip install -r requirements.txt`
- `python main.py`

Optionally, you can provide a log file, or folder with multiple log files.
The script will automatically load those in. You also manually do it later.

Made in Python 3.9
