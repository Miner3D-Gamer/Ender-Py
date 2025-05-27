import shutil


__all__ = ["fast_copytree", "fast_rmtree"]


def fast_copytree(src: str, dst: str) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def fast_rmtree(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)
