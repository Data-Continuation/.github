python resident-runtime/tests/test_resident_boundary_executor.py
tmpdir="$(mktemp -d)"
python resident-runtime/resident_boundary_executor.py --state-root "$tmpdir/state" --validate-layout
