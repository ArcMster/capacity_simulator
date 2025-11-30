import re

file_path = '/home/sreenath/My projects/Cap/capacity_proj/capacity_tracking/templates/capacity_tracking/search_schedule.html'

with open(file_path, 'r') as f:
    content = f.read()

# Regex to find {{ followed by whitespace/newlines and then content, and }}
# We want to collapse {{ \s+ variable \s+ }} into {{ variable }}
# But we need to be careful not to break things.
# Simplest approach: Replace {{ \n + with {{ 

# Pattern 1: {{ at end of line
# content = re.sub(r'\{\{\s*\n\s*', '{{ ', content)

# Pattern 2: variable \n \s* }}
# content = re.sub(r'\s*\n\s*\}\}', ' }}', content)

# Let's try a more robust approach:
# Find all {{ ... }} blocks that might span lines and normalize them.
def normalize_tag(match):
    text = match.group(0)
    # Replace newlines and multiple spaces with a single space
    return re.sub(r'\s+', ' ', text)

# Regex for {{ ... }} spanning multiple lines
# Non-greedy match until }}
content = re.sub(r'\{\{.*?\}\}', normalize_tag, content, flags=re.DOTALL)

# Also do it for {% ... %} just in case
content = re.sub(r'\{%.*?%\}', normalize_tag, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

print("Template tags normalized.")
