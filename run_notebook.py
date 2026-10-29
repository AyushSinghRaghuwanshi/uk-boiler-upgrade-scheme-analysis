"""Execute the notebook in this interpreter, using a temporary kernel specification.

Run with .venv/Scripts/python.exe run_notebook.py on Windows.
No global or user-level Jupyter kernel installation is required.
"""

from pathlib import Path
import json
import os
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

root = Path(__file__).resolve().parent
assert Path(sys.prefix).resolve() == (root / ".venv").resolve(), "Use the project .venv Python"
notebook_path = root / "notebooks" / "01_data_understanding.ipynb"
notebook = nbformat.read(notebook_path, as_version=4)
for variable in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
]:
    os.environ[variable] = "1"
os.environ["PYTHONHASHSEED"] = "42"

with tempfile.TemporaryDirectory(prefix="icf-kernel-") as temporary:
    kernel_dir = Path(temporary) / "project-venv"
    kernel_dir.mkdir()
    (kernel_dir / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "Project .venv",
                "language": "python",
            }
        )
    )
    manager = KernelManager(
        kernel_name="project-venv", kernel_spec_manager=KernelSpecManager(kernel_dirs=[temporary])
    )
    client = NotebookClient(
        notebook,
        km=manager,
        timeout=600,
        resources={"metadata": {"path": str(root)}},
        record_timing=True,
    )
    client.on_cell_complete = lambda cell, cell_index, **kwargs: print(
        f"Completed cell {cell_index + 1}/{len(notebook.cells)}", flush=True
    )
    try:
        client.execute()
    finally:
        nbformat.write(notebook, notebook_path)
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)

errors = [
    o
    for c in notebook.cells
    if c.cell_type == "code"
    for o in c.get("outputs", [])
    if o.output_type == "error"
]
assert not errors, errors
print("Notebook executed successfully:", notebook_path)
