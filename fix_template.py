import os

file_path = '/home/sreenath/My projects/Cap/capacity_proj/capacity_tracking/templates/capacity_tracking/search_schedule.html'

with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = False

for i in range(len(lines)):
    if skip_next:
        skip_next = False
        continue
    
    line = lines[i]
    # Check for the specific split tag pattern
    if 'onclick="toggleDetails' in line and '{% if' in line and not '%}' in line:
        # It's the split line!
        next_line = lines[i+1]
        combined = line.rstrip() + ' ' + next_line.lstrip()
        new_lines.append(combined)
        skip_next = True
        print(f"Fixed split tag at line {i+1}")
    else:
        new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print("File rewritten successfully.")
