import os
import glob

def replace_in_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Thay thế các dạng chữ
    new_content = content.replace('chitchat', 'ignore')
    new_content = new_content.replace('CHITCHAT', 'IGNORE')
    new_content = new_content.replace('Chitchat', 'Ignore')
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {path}")

# Duyệt toàn bộ code trong src và scripts
for f in glob.glob('src/**/*.py', recursive=True):
    replace_in_file(f)
    
for f in glob.glob('scripts/**/*.py', recursive=True):
    replace_in_file(f)
