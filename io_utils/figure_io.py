from pathlib import Path

def save_figure(fig, run_dir, name, dpi = 300):
    fig_dir = Path(run_dir) / "figures"
    fig_dir.mkdir(exist_ok=True)

    path = fig_dir / f"{name}.png"
    fig.savefig(path, dpi = dpi, bbox_inches="tight")
    print(f"Saved figure: {path}")
