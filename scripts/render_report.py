import subprocess

print("Rendering RMarkdown report...")

command = [
    "Rscript",
    "-e",
    """
    rmarkdown::render(
        'reports/analysis.Rmd',
        output_file='report.html',
        output_dir='reports/output'
    )
    """
]

subprocess.run(command, check=True)

print("Report generated.")