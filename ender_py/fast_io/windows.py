import os
import shutil
import subprocess

__all__ = ["fast_copytree", "fast_rmtree"]


def fast_copytree(src: str, dst: str) -> None:
    result = subprocess.run(
        [
            "robocopy",
            src,
            dst,
            "/E",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
            "/NP",
            "/MT:8",
        ],
        shell=True,
    )
    if result.returncode >= 8:
        print(f"robocopy failed with code {result.returncode}")
        shutil.copytree(src, dst, dirs_exist_ok=True)


from .fallback import fast_rmtree

# THESE FUNCTIONS IS TOO SLOW, WHY IS BUILT IN BETTER???

# import tempfile


# def fast_rmtree(path: str) -> None:
#     with tempfile.TemporaryDirectory() as empty_dir:
#         result = subprocess.run(
#             ["robocopy", empty_dir, path, "/MIR", "/NJH", "/NJS", "/NP", "/NFL"],
#             creationflags=subprocess.CREATE_NO_WINDOW,
#         )
#         # robocopy returns 0 or 1 for success, treat other codes as failure
#         if result.returncode > 1:
#             print(f"robocopy failed with code {result.returncode}, falling back")
#             shutil.rmtree(path, ignore_errors=True)
#         else:
#             # Finally remove the directory itself
#             os.rmdir(path)


# def fast_rmtree(path: str) -> None:
#     norm_path = os.path.normpath(path)

#     # PowerShell with optimized parameters for many small files
#     result = subprocess.run(
#         [
#             "powershell",
#             "-NoProfile",
#             "-Command",
#             f"Remove-Item -LiteralPath '{norm_path}' -Recurse -Force",
#         ],
#         creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
#     )

#     if result.returncode != 0:
#         print(f"powershell failed with code {result.returncode}")
#         shutil.rmtree(norm_path, ignore_errors=True)
