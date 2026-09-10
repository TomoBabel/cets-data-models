"""Regenerate in scratch storage and require a byte-identical public model."""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix="cets-model-generation-") as directory:
    generated = Path(directory) / "models.py"
    subprocess.run([sys.executable, str(root / "model_processing/generate_models.py"), str(generated)], check=True, cwd=root)
    committed = root / "src/cets_data_model/models/models.py"
    if generated.read_bytes() != committed.read_bytes():
        raise SystemExit("Public models differ from LinkML + generator configuration; run make gen-python")
print("Public models reproduce exactly")
