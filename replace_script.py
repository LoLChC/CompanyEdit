import sys

file_path = r"C:\Users\lolch\Desktop\CompanyEdit\yonetim\views.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import re

# We will use regex to replace the is_kurum function
pattern = re.compile(r"def is_kurum\(unvan\):.*?return False", re.DOTALL)
content = pattern.sub("def is_kurum(unvan):\n    return True", content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
