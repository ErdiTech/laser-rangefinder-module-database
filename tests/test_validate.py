import subprocess, sys, os
def test_validate():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    r = subprocess.run([sys.executable, os.path.join(here, "scripts/validate.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
