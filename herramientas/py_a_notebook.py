"""Convierte trabajo_final.py (celdas # %% / # %% [markdown]) en trabajo_final.ipynb.

Uso (desde neurociencias/):  py -3.12 herramientas/py_a_notebook.py trabajo_final.py trabajo_final.ipynb
Después, para ejecutarlo y guardar las salidas:
    py -3.12 -m jupyter nbconvert --to notebook --execute --inplace trabajo_final.ipynb
"""
import re, sys, nbformat
src = open(sys.argv[1], encoding="utf-8").read()
parts = re.split(r"^(# %%.*)$", src, flags=re.M)
nb = nbformat.v4.new_notebook()
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
hdr = None
for p in parts:
    if p.startswith("# %%"):
        hdr = p; continue
    body = p.strip("\n")
    if hdr is None or not body.strip():
        continue
    if "[markdown]" in hdr:
        md = "\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.splitlines())
        nb.cells.append(nbformat.v4.new_markdown_cell(md))
    else:
        nb.cells.append(nbformat.v4.new_code_cell(body))
nbformat.write(nb, sys.argv[2])
print(len(nb.cells), "celdas")
