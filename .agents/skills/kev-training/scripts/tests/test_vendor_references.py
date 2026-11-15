"""Relocated upstream packages stay complete and usable without Modal or network."""
import pytest
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import training_plan as planner


class TestVendorReference:
    @pytest.mark.parametrize('name,root', list(planner.VENDOR_ROOTS.items()))
    def test_complete_packages_and_licenses_match_fixed_manifests(self, name, root):
        identities = planner.verify_vendor()
        assert (set(identities)) == ({"kev-finetune"})
        manifest = json.loads((root / "UPSTREAM.json").read_text())
        expected = {item["path"] for item in manifest["upstream_files"]}
        expected.update(manifest["local_additions"])
        actual = {str(path.relative_to(root)) for path in root.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts}
        assert (actual) == (expected)
        assert (len(manifest["upstream_files"])) == (manifest["verification"]["original_file_count"])
        license_info = manifest["license"]
        assert (hashlib.sha256((root / license_info["local_path"]).read_bytes()).hexdigest()) == (license_info["sha256"])

    def test_vendor_byte_change_still_blocks_training_preparation(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = {}
            for name, root in planner.VENDOR_ROOTS.items():
                copied[name] = Path(temporary) / name
                shutil.copytree(root, copied[name], ignore=shutil.ignore_patterns("__pycache__"))
            altered = copied["kev-finetune"] / "README.md"
            altered.write_bytes(altered.read_bytes() + b"\nsynthetic tampering\n")
            with patch.object(planner, "VENDOR_ROOTS", copied):
                with pytest.raises(ValueError, match="vendor_file_changed: kev-finetune/README.md"):
                    planner.verify_vendor()

    @pytest.mark.parametrize('case_index_1', range(5))
    def test_official_local_helpers_resolve_sibling_imports_from_another_cwd(self, case_index_1):
        scripts = planner.VENDOR_ROOTS['kev-finetune'] / 'scripts'
        with tempfile.TemporaryDirectory() as temporary:
            filename = tuple(('convert_data.py', 'generate_data.py', 'extract_workload.py', 'plan_size.py', 'split_data.py'))[case_index_1]
            result = subprocess.run([sys.executable, str(scripts / filename), '--help'], cwd=temporary, capture_output=True, text=True, timeout=15)
            assert result.returncode == 0, result.stderr
            assert 'usage:' in result.stdout.lower()
            assert list(Path(temporary).iterdir()) == []
