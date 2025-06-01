import re
import json

from .internal_shared import (
    jp,
    replace,
    combine_dicts,
)
from shared import (
    log,
    FATAL,
)

from fast_functions import *

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mod_class import Mod, ModInfo


def is_valid_internal_mod_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm._":
            return False
    if id.__contains__(".."):
        return False
    if len(id) > 255:
        return False

    return True


def is_valid_external_mod_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm_-0123456789":
            return False
    if id.__contains__(".."):
        return False
    if len(id) > 255:
        return False

    return True


def is_valid_component_id(id: str):
    if not id.islower():
        return False
    for char in id:
        if char not in "qwertzuiopasdfghjklyxcvbnm_":
            return False
    if len(id) > 255:
        return False

    return True


def assemble_pack(
    resource_path: str,
    template_path: str,
    final_cache_path: str,
    mod_id: str,
    mod: "Mod",
    mod_info: "ModInfo",
    info_replace: dict[str, str],
):
    copy_and_rename_builtin(resource_path, template_path, mod_id)

    required_file = jp(template_path, "required.json")
    if not os.path.exists(required_file):
        log(
            FATAL,
            f"Required file {required_file} does not exist, files like mod.toml and pack.mcmeta should be defined here.",
        )

    required_files = json.loads(get_file_contents(required_file))
    for file, format in required_files.items():
        path = jp(template_path, file)
        if not os.path.exists(path):
            log(
                FATAL,
                f"Required file {path} does not exist (Declared in {required_file})",
            )
        os.makedirs(jp(final_cache_path, os.path.dirname(file)), exist_ok=True)
        file_contents = get_file_contents(jp(template_path, file))

        if format:
            file_contents = format_text(file_contents, mod, mod_info, info_replace)

        write_to_file(jp(final_cache_path, file), file_contents)


def format_text(
    text: str,
    mod: "Mod",
    mod_info: "ModInfo",
    info_replace: dict[str, str],
    additional_replace: dict[str, str] = {},
) -> str:
    return replace(
        text,
        combine_dicts(
            combine_dicts(
                {
                    "mod_id": mod.id,
                    "internal_mod_id": mod.internal_id,
                    "mod_id_upper": mod.id.title(),
                    "mod_name": mod.name,
                    "author": mod.author,
                    "description": mod.description,
                    "version": mod.version,
                    "mod_version": mod.version,
                    "homepage": mod.homepage,
                    "minecraft_version": mod_info["minecraft_version"],
                    "mod_loader_version": mod_info["mod_loader_version"],
                },
                info_replace,
            ),
            additional_replace,
        ),
    )


def get_all_models_in_blockstate(blockstate: str):
    return re.findall('"model": "(.*?)"', blockstate)
