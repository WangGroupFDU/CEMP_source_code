from pathlib import Path


def gjf_to_xyz(gjf_path):
    gjf_path = Path(gjf_path)
    lines = gjf_path.read_text().splitlines()

    atoms = []

    
    start_idx = None
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        parts = s.split()
        
        if s[0] in "+-0123456789" and len(parts) == 2:
            start_idx = i + 1
            break

    if start_idx is None:
        raise RuntimeError("Could not find charge/multiplicity line in " + str(gjf_path))

    
    for line in lines[start_idx:]:
        if not line.strip():
            break
        parts = line.split()
        if len(parts) < 4:
            break
        sym = parts[0]
        x, y, z = map(float, parts[1:4])
        atoms.append((sym, x, y, z))

    if not atoms:
        raise RuntimeError("No atom coordinates found in " + str(gjf_path))

    
    xyz_path = gjf_path.with_suffix(".xyz")
    with xyz_path.open("w") as f:
        f.write(f"{len(atoms)}\n")
        f.write(f"{gjf_path.stem}\n")
        for sym, x, y, z in atoms:
            f.write(f"{sym:2s} {x:15.6f} {y:15.6f} {z:15.6f}\n")

    print("Wrote", xyz_path)


if __name__ == "__main__":
    
    for name in ["cis_2butene.gjf", "trans_2butene.gjf"]:
        p = Path(name)
        if p.exists():
            gjf_to_xyz(p)
        else:
            print("Skip (file not found):", p)
