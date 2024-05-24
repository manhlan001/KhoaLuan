def parse_labels(input_lines):
    labels = {}
    current_label = None
    remaining_lines = []

    for line in input_lines:
        stripped_line = line.strip()
        
        if stripped_line.endswith(':'):
            current_label = stripped_line[:-1]
            labels[current_label] = []
        elif current_label is not None:
            labels[current_label].append(stripped_line)
            remaining_lines.append(stripped_line)
    
    return labels, remaining_lines

# Example usage
input_lines = [
    "label1:",
    "line1",
    "line2",
    "label2:",
    "line3",
    "line4",
    "line5",
    "label3:",
    "line6",
    "label4:"
]

labels, remaining_lines = parse_labels(input_lines)

# Display labels and their lines
for label, lines in labels.items():
    print(f"{label}: {lines}")

# Display remaining lines
print("Remaining lines:", remaining_lines)

# Example of accessing a specific label
label_name = "label2"
if label_name in labels:
    print(f"Lines under {label_name}: {labels[label_name][0]}")
else:
    print(f"{label_name} not found")
    
i = 0
visited = set()

while i < 10:
    print(i)
    
    # Thêm i vào tập hợp visited để tránh lặp lại vô hạn
    if i in visited:
        break
    visited.add(i)
    
    # Logic thay đổi giá trị của i
    if i == 5:
        i = 2  # Quay lại giá trị 2 khi i bằng 5
    else:
        i += 1

