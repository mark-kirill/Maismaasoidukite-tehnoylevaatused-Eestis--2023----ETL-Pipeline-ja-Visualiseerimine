import subprocess

scripts = [
    "scripts/download_csv.py",
    "scripts/clean_csv.py",
    "scripts/csv_to_sqlite.py",
    "scripts/render_report.py"
]

for script in scripts:
    print(f"\nRunning: {script}")

    result = subprocess.run(
        ["python", script],
        check=True
    )

print("\nPipeline completed successfully.")