import shutil
import subprocess

if shutil.which("rsync"):

    def fast_copytree(src: str, dst: str) -> None:
        result = subprocess.run(
            ["rsync", "-a", "--info=NONE", "--no-i-r", f"{src}/", dst]
        )
        if result.returncode != 0:
            print(f"rsync failed with code {result.returncode}")
            shutil.copytree(src, dst, dirs_exist_ok=True)

else:
    from .fallback import fast_copytree


def fast_rmtree(path: str) -> None:
    result = subprocess.run(["rm", "-rf", path])
    if result.returncode != 0:
        print(f"rm failed with code {result.returncode}, using fallback")
        shutil.rmtree(path, ignore_errors=True)


__all__ = ["fast_copytree", "fast_rmtree"]
