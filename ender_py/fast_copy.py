# import os
import shutil
import subprocess
import platform
from .shared import log, ERROR

system = platform.system()


if system == "Windows":
    # A speed increase of over 20 seconds to under 1 second, wtf (~3000 Files)

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
            log(ERROR, f"robocopy failed with code {result.returncode}, using fallback")
            shutil.copytree(src, dst, dirs_exist_ok=True)

elif system in ["Linux", "Darwin"]:
    if shutil.which("rsync"):

        def fast_copytree(src: str, dst: str) -> None:
            result = subprocess.run(
                ["rsync", "-a", "--info=NONE", "--no-i-r", f"{src}/", dst]
            )
            if result.returncode != 0:
                log(
                    ERROR, f"rsync failed with code {result.returncode}, using fallback"
                )
                shutil.copytree(src, dst, dirs_exist_ok=True)

    else:

        def fast_copytree(src: str, dst: str) -> None:
            shutil.copytree(src, dst, dirs_exist_ok=True)

else:

    def fast_copytree(src: str, dst: str) -> None:
        shutil.copytree(src, dst, dirs_exist_ok=True)
