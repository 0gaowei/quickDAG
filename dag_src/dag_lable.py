import re

# Define a function to process the DOT file and add labels
def add_labels_to_dot_file(input_file_path, output_file_path):
    # Read the content of the input DOT file
    with open(input_file_path, 'r') as file:
        dot_content = file.read()
    
    # Add labels to nodes (size)
    updated_dot = re.sub(r'(\d+)\s*\[size="(\d+)",\s*alpha="([\d\.]+)"\]', 
                         r'\1 [size="\2", alpha="\3", label="Index: \1 \n Time: \2"]', dot_content)
    
    # Add labels to edges (size)
    updated_dot = re.sub(r'(\d+)\s*->\s*(\d+)\s*\[size ="(\d+)"\]', 
                         r'\1 -> \2 [size="\3", label="MEM: \3"]', updated_dot)
    
    # Write the updated content to the output DOT file
    with open(output_file_path, 'w') as output_file:
        output_file.write(updated_dot)

    print(f"Modified DOT content saved to {output_file_path}")

# File paths
input_file_path = 'dag-default.txt'  # Replace with your actual file path
output_file_path = 'modified_dag.dot'

# Process the DOT file
add_labels_to_dot_file(input_file_path, output_file_path)
