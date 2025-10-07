import re
import os

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        cleaned_lines = []
        in_docstring = False
        
        for line in lines:
            stripped = line.strip()
            
            if '"""' in line or "'''" in line:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = not in_docstring
                    continue
            
            if in_docstring:
                continue
            
            if stripped.startswith('#') and not stripped.startswith('#!'):
                continue
            
            if '#' in line and not line.strip().startswith('#'):
                line = re.sub(r'\s*#[^"\']*$', '', line)
            
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"✓ {filepath}")
    except Exception as e:
        print(f"✗ {filepath}: {e}")

for root, dirs, files in os.walk('bot'):
    for file in files:
        if file.endswith('.py'):
            clean_file(os.path.join(root, file))

print("\nГотово!")

