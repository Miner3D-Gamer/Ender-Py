import os


def find_files_with_extension(root_dir: str, file_extension: str):
    file_paths = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(file_extension):
                file_paths.append(os.path.join(root, file))
    return file_paths


extra = ["/procedure_crafter", "/bobstruct", "/ender_py/cache"]

with open(".gitignore", "w") as f:
    f.write(
        "\n".join(extra)
        + "\n"
        + "\n".join(
            [
                file[2:].replace("\\", "/")
                for file in find_files_with_extension("./", ".pyc")
            ]
        )
    )
