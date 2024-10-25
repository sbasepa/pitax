import re
import os
import sys
# Define regex patterns for key-value pairs and blocks
TOKEN_KEY_VALUE = re.compile(r'(?P<key>"[^"]+")\s*:\s*(?P<value>"[^"]*"|\{)')  # Matches key-value pairs
TOKEN_KEY_BLOCK = re.compile(r'(?P<key>"[^"]+")\s*=\s*\{')  # Matches keys followed by blocks like key={
TOKEN_IDENTIFIER = re.compile(r'"[^"]+"')  # Matches quoted identifiers
TOKEN_EXPORT = re.compile(r'export\((?P<filename>"[^"]+")\)')  # Matches the export statement

# Function to parse a line that is a key-value pair like 'key: "value"'
def parse_key_value(line):
    match = TOKEN_KEY_VALUE.match(line)
    if match:
        key = match.group("key").strip('"')  # Remove quotes from the key
        value = match.group("value").strip()  # Get the value, which is either a string or a block
        if value == '{':
            return key, {}  # Return an empty dict for blocks
        else:
            return key, value.strip('"')  # Return the value without quotes
    return None  # If no match, return None

# Function to import a configuration from another file
def import_config(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file {file_path} not found.")
    
    with open(file_path, 'r') as f:
        return f.read().strip()  # Read and return the content of the file

# Recursive function to parse a block of configuration, e.g., a section inside {...}
def parse_block(lines, index, defined_keys):
    block = {}  # Dictionary to store the parsed block
    while index < len(lines):  # Iterate through lines until the block is closed
        line = lines[index].strip()  # Strip whitespace from the line
        
        # Check for export statements
        export_match = TOKEN_EXPORT.match(line)
        if export_match:
            filename = export_match.group("filename").strip('"')  # Get the filename from the export statement
            imported_config = import_config(filename)  # Import the config from the specified file
            imported_lines = imported_config.splitlines()  # Split the imported config into lines
            # Parse each line from the imported config
            imported_config_dict = parse_config_lines(imported_lines)  # Recursive call to parse
            block.update(imported_config_dict)  # Merge imported config into the current block
            
        elif line == '}':  # If we encounter a closing brace, the block is done
            return block, index  # Return the block and the current index
        
        # Attempt to parse the line as a key-value pair or block
        if line.endswith('{'):
            match = TOKEN_KEY_BLOCK.match(line)
            if match:
                key = match.group("key").strip('"')  # Extract the key
                if key in defined_keys:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {key}")
                defined_keys.add(key)  # Add key to defined keys
                block[key], index = parse_block(lines, index + 1, defined_keys)  # Recursively parse the nested block
        else:
            key_val = parse_key_value(line)  # Try parsing the line as a key-value pair
            if key_val:
                key, value = key_val  # If successful, add the key-value pair to the block
                if key in defined_keys:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {key}")
                defined_keys.add(key)  # Add key to defined keys
                block[key] = value
            elif TOKEN_IDENTIFIER.match(line):  # If it's just a key without a value, add it as a key with None
                if line.strip('"') in defined_keys:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {line.strip()}")
                block[line.strip('"')] = None  # Add the key without a value
                defined_keys.add(line.strip('"'))  # Add key to defined keys
        
        index += 1  # Move to the next line
    raise ValueError("Unclosed block")  # Raise an error for unclosed blocks

# Function to parse configuration lines
def parse_config_lines(lines):
    config = {}  # Dictionary to store the entire parsed configuration
    index = 0  # Line index

    # Loop through each line in the configuration
    while index < len(lines):
        line = lines[index].strip()  # Strip whitespace from the line
        if not line:  # Skip empty lines
            index += 1
            continue
        
        # Attempt to parse the line as a key-value pair or block
        if line.endswith('{'):
            match = TOKEN_KEY_BLOCK.match(line)
            if match:
                key = match.group("key").strip('"')  # Extract the key
                if key in config:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {key}")
                config[key], index = parse_block(lines, index + 1, {key})  # Parse the block recursively
        else:
            key_val = parse_key_value(line)  # Try parsing the line as a key-value pair
            if key_val:
                key, value = key_val  # If it's a key-value pair, add it to the config dictionary
                if key in config:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {key}")
                config[key] = value
            elif TOKEN_IDENTIFIER.match(line):  # If it's just a key without a value, add it as a key
                if line.strip('"') in config:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {line.strip()}")
                config[line.strip('"')] = None  # Add the key without a value

        index += 1  # Move to the next line

    return config  # Return the final parsed configuration

# Main function to parse the whole configuration file
def parse_config(file_path):
    os.chdir('/root/k/pitax/config')
    with open(file_path, 'r') as f:
        lines = f.readlines()  # Read all lines from the file

    config = {}  # Dictionary to store the entire parsed configuration
    index = 0  # Line index

    # Skip the identifier line


    # Loop through each line in the configuration
    while index < len(lines):
        line = lines[index].strip()  # Strip whitespace from the line
        if not line:  # Skip empty lines
            index += 1
            continue
        
        # Attempt to parse the line as a key-value pair or block
        if line.endswith('{'):
            match = TOKEN_KEY_BLOCK.match(line)
            if match:
                key = match.group("key").strip('"')  # Extract the key
                if key in config:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {key}")
                config[key], index = parse_block(lines, index + 1, {key})  # Parse the block recursively
        else:
            key_val = parse_key_value(line)  # Try parsing the line as a key-value pair
            if key_val:
                key, value = key_val  # If it's a key-value pair, add it to the config dictionary
                if key in config:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {key}")
                config[key] = value
            elif TOKEN_IDENTIFIER.match(line):  # If it's just a key without a value, add it as a key
                if line.strip('"') in config:  # Check for duplicate keys
                    raise ValueError(f"Duplicate key found: {line.strip()}")
                config[line.strip('"')] = None  # Add the key without a value

        index += 1  # Move to the next line

    return config  # Return the final parsed configuration

# Example usage
def main(config_file):
    # Assuming your configuration file is named 'pitax.conf'
    try:
        # Parse the configuration file
        return parse_config(config_file)

        # Print the parsed configuration dictionary to check the result
    except Exception as e:
        print(f"Error parsing configuration: {e}")
        
