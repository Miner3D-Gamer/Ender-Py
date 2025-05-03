import tge

with open(".gitignore", "w") as f:
    f.write(
        "/procedure_crafter"
        + "\n"
        + "\n".join(
            [
                file[2:].replace("\\", "/")
                for file in tge.file_operations.find_files_with_extension(".", ".pyc")
            ]
        )
    )
