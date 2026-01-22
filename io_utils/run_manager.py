from pathlib import Path
from datetime import datetime

def create_run_folder(run_name, base_dir="results"):
    base_dir = Path(base_dir)
    base_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_name = f"{timestamp}_{run_name}"

    run_dir = base_dir / base_name

    if not run_dir.exists():
        run_dir.mkdir()
    else:
        i = 0
        while True:
            candidate = base_dir / f"{base_name}_{i:03d}"
            if not candidate.exists():
                run_dir = candidate
                run_dir.mkdir()
                break
            i += 1

    (run_dir / "figures").mkdir()
    print("Creating run folder:", run_name)

    return run_dir
