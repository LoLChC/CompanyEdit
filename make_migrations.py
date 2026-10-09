import os
import subprocess

os.chdir(r"C:\Users\lolch\Desktop\CompanyEdit")
try:
    result = subprocess.run(["python", "manage.py", "makemigrations"], capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except Exception as e:
    print("ERROR:", e)
