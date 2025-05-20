# IMPORTS AND CONTEXTS ARE NOT RESPECTED DUE TO THE NEW STRUCTURE

import json, os
from ender_py.shared import (
    log,
    FATAL,
    ERROR,
    WARNING,
    INFO,
    get_file_contents,
    jp,
    replace,
)
from typing import Any, Optional, TypedDict, NoReturn, Union, TypeVar, Type

T = TypeVar("T")


def get(
    dictionary: dict,
    key: str,
    default: Any = None,
    name: Optional[str] = None,
    _searched: Optional[Type[T]] = None,  # This is such python trickery
) -> Union[NoReturn, T]:
    warn = True
    if not key in dictionary:
        if default is None:
            log(
                FATAL,
                f"Key '{key}' not found in '{dictionary if name is None else name}'",
            )
        if warn:
            log(
                WARNING,
                f"Key '{key}' not found in '{dictionary if name is None else name}', using default '{default}'",
            )
        return default
    return dictionary[key]


def combine_dicts(dict1: dict, dict2: dict) -> dict[str, str]:
    return {**dict1, **dict2}


class Block(TypedDict):
    # type: str
    name: str
    version_instance: dict[str, "VersionInstance"]
    inputs: list[dict[str, str]]
    output: str


def get_subfolders_of_folder(folder_path: str) -> list[str]:
    return [
        folder
        for folder in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, folder))
    ]


class Event(TypedDict):
    name: str
    version_instance: dict[str, "VersionInstance"]
    given_contexts: list[str]


class VersionInstance(TypedDict):
    file: str
    required_imports: list[str]
    required_contexts: list[str]


class Context(TypedDict):
    name: str
    version_instance: dict[str, VersionInstance]


def get_full_everything(
    procedure_blocks_path: str, folder: str, yep: dict, setting_name: str
) -> dict[str, VersionInstance]:
    new = {}
    if not isinstance(yep, dict):
        raise Exception(
            "Expected input to be a dict for file but got %s for %s"
            % (yep, setting_name)
        )

    for key, value in yep.items():
        # if not isinstance(value, dict):
        #     log(
        #         FATAL,
        #         "Expected specified file to be in format {'file':'path'} for %s"
        #         % setting_name,
        #     )

        new[key] = VersionInstance(
            file=jp(os.getcwd(), procedure_blocks_path, folder, value["file"]),
            required_imports=value.get("required_imports", []),
            required_contexts=value.get("required_contexts", []),
        )

    return new


class ProcedureInternal:
    def __init__(self): ...

    def load_blocks(self, procedure_blocks_path: str):
        self.procedure_blocks_path = procedure_blocks_path
        self.blocks: list[Block] = []
        self.events: list[Event] = []
        self.contexts = []
        for folder in get_subfolders_of_folder(procedure_blocks_path):
            with open(
                os.path.join(procedure_blocks_path, folder, "settings.json"), "r"
            ) as f:
                settings = json.load(f)

            for block in settings["blocks"]:
                type = block.get("type")
                if type is None:
                    log(ERROR, f"Block {block} in {folder} has no type")
                if type == "event":
                    new = Event(
                        name=get(block, "name", _searched=str),
                        version_instance=get_full_everything(
                            procedure_blocks_path,
                            folder,
                            get(
                                block,
                                "versions",
                                _searched=dict[str, str | list[str]],
                            ),
                            block["name"],
                        ),
                        given_contexts=get(
                            block,
                            "given_contexts",
                            [],
                            block["name"],
                            _searched=list[str],
                        ),
                    )
                    self.events.append(new)
                elif block["type"] == "context":
                    new = Context(
                        name=get(block, "name", _searched=str),
                        version_instance=get_full_everything(
                            procedure_blocks_path,
                            folder,
                            get(
                                block,
                                "versions",
                                _searched=dict[str, str | list[str]],
                            ),
                            block["name"],
                        ),
                    )
                    self.contexts.append(new)
                elif block["type"] in ["action", "inline"]:
                    new = Block(
                        name=get(block, "name", _searched=str),
                        version_instance=get_full_everything(
                            procedure_blocks_path,
                            folder,
                            get(
                                block,
                                "versions",
                                _searched=dict[str, str | list[str]],
                            ),
                            block["name"],
                        ),
                        output=get(
                            block, "output", "none", block["name"], _searched=str
                        ),
                        inputs=get(
                            block,
                            "inputs",
                            [],
                            block["name"],
                            _searched=list[dict[str, str]],
                        ),
                    )
                    self.blocks.append(new)
                else:
                    log(ERROR, f"Block {block} in {folder} has unknown type {type}")
                    # new = {
                    #     "name": get(block, "name"),
                    #     "required_imports": get(block, "required_imports", [], block["name"]),
                    #     "required_contexts": get(block, "required_contexts", [], block["name"]),
                    #     "file": get(block, "file", block["name"]),
                    #     "output": get(block, "output", "none", block["name"]),
                    #     "inputs": get(block, "inputs", [], block["name"])
                    # }

    def pre_event(
        self,
        requested_version: str,
        events: list[Event],
        event: str,
    ):
        self.current_contexts: list[str] = []
        self.required_imports: list[str] = []
        self.required_contexts = []
        if event == "none":
            self.event_code = "{imports}\npublic static void none(){{code}}"
        else:
            for i in events:
                if i["name"] == event:
                    self.required_imports.extend(
                        i["version_instance"][requested_version]["required_imports"]
                    )
                    self.current_contexts.extend(i["given_contexts"])
                    self.event_code = get_file_contents(
                        i["version_instance"][requested_version]["file"]
                    )
                    break
            else:
                log(FATAL, f"Event {event} not found")

    def does_throughput_match(self, lower: dict, higher: dict):
        return lower["type"] == higher["output"]

    def handle_block(
        self,
        procedure_data: dict[str, Any],
        requested_version: str,
        block_data: list[Block],
    ) -> Union[NoReturn, dict]:
        for b in block_data:
            if procedure_data == {}:
                log(FATAL, "Procedure is empty")
            if procedure_data.get("action") is None:
                log(
                    FATAL,
                    "Procedure has no action or something IDK specified: %s"
                    % (procedure_data),
                )
            if b["name"] == procedure_data["action"]:
                inputs = b["inputs"]
                contents = get_file_contents(
                    b["version_instance"][requested_version]["file"]
                )
                # REMOVE THIS
                self.required_imports.extend(
                    b["version_instance"][requested_version]["required_imports"]
                )
                self.required_contexts.extend(
                    b["version_instance"][requested_version]["required_contexts"]
                )
                if inputs == []:
                    return {
                        "required_imports": b["version_instance"][requested_version][
                            "required_imports"
                        ],
                        "required_contexts": b["version_instance"][requested_version][
                            "required_contexts"
                        ],
                        "file_contents": contents,
                        "output": b["output"],
                    }
                for singular_expected_input in inputs:
                    type = singular_expected_input["type"]
                    if type == "literal":
                        allowed = singular_expected_input["expected"]
                        if isinstance(allowed, dict):
                            wanted_input = procedure_data.get(
                                singular_expected_input["name"]
                            )
                            if wanted_input is None:
                                log(
                                    FATAL,
                                    f"[Procedure] An input was wrongly defined: {singular_expected_input['name']} in block {procedure_data['action']}",
                                )
                            inp = wanted_input
                            if inp not in allowed:
                                log(
                                    FATAL,
                                    f"Expected one of {[x for x in allowed]} but got {inp} in block {procedure_data['action']}",
                                )
                            given = {
                                "file_contents": allowed[inp],
                                "required_imports": b["version_instance"][
                                    requested_version
                                ]["required_imports"],
                                "required_contexts": b["version_instance"][
                                    requested_version
                                ]["required_contexts"],
                                "info": 1,
                            }
                        elif isinstance(allowed, list):
                            log(
                                FATAL,
                                "Hi there, no clue what went wrong for this error to show up",
                            )
                        elif isinstance(allowed, str):
                            if allowed == "str":
                                if isinstance(
                                    procedure_data[singular_expected_input["name"]], str
                                ):
                                    given = {
                                        "file_contents": f'"{procedure_data[singular_expected_input["name"]]}"',
                                        "required_imports": b["version_instance"][
                                            requested_version
                                        ]["required_imports"],
                                        "required_contexts": b["version_instance"][
                                            requested_version
                                        ]["required_contexts"],
                                        "info": 2,
                                    }
                                else:
                                    log(
                                        FATAL,
                                        f"Expected a string but got {procedure_data[singular_expected_input['name']]} in block {procedure_data['action']}",
                                    )
                            else:
                                log(FATAL, "Expected allowed to be str")
                        else:
                            log(
                                FATAL,
                                "Expected 'literal' to be a string, dict, or list",
                            )
                    else:
                        next = procedure_data.get(singular_expected_input["name"])
                        if next == {}:
                            log(
                                FATAL,
                                "Did you forget to complete a %s block?"
                                % singular_expected_input["name"],
                            )
                        if next is None:
                            log(
                                FATAL,
                                f"Input '{singular_expected_input['name']}' not found in block '{procedure_data['action']}' (Procedure)",
                            )
                        if isinstance(next, list):
                            sub_contents = ""
                            further_required_imports = []
                            further_required_contexts = []
                            for n in next:
                                next_given = self.handle_block(
                                    n, requested_version, block_data
                                )

                                sub_contents += next_given["file_contents"]
                                further_required_imports.extend(
                                    next_given["required_imports"]
                                )
                                further_required_contexts.extend(
                                    next_given["required_contexts"]
                                )
                            given = {
                                "file_contents": sub_contents,
                                "required_imports": further_required_imports,
                                "required_contexts": further_required_contexts,
                                "info": 3,
                            }
                        elif isinstance(next, str):
                            given = {
                                "file_contents": next,
                                "required_imports": b["version_instance"][
                                    requested_version
                                ]["required_imports"],
                                "required_contexts": b["version_instance"][
                                    requested_version
                                ]["required_contexts"],
                                "info": 4,
                            }
                        else:
                            # Next is block data
                            given = self.handle_block(
                                next, requested_version, block_data
                            )
                            if not self.does_throughput_match(
                                singular_expected_input, given
                            ):
                                log(
                                    FATAL,
                                    f"Expected throughput '{singular_expected_input['type']}' but got throughput '{given['output']}' between blocks '{procedure_data['action']}' and '{next['action']}'",
                                )
                    contents = replace(
                        contents,
                        {singular_expected_input["name"]: given["file_contents"]},
                    )

                if not isinstance(given["required_imports"], list):
                    log(
                        FATAL,
                        "Expected required_imports to be a list but got %s (full: %s)"
                        % (given["required_imports"], given),
                    )

                return {
                    "required_imports": (
                        b["version_instance"][requested_version]["required_imports"]
                        + given["required_imports"]
                    ),
                    "required_contexts": (
                        b["version_instance"][requested_version]["required_contexts"]
                        + given["required_contexts"]
                    ),
                    "file_contents": contents,
                    "output": b["output"],
                }
        log(
            FATAL,
            f"Block '{procedure_data['action']}' not found (Not defined within any loaded plugins)",
        )

    def handle_event(self, procedure: list, requested_version: str, event: str):
        """
        return: Tuple[Event code, required imports, context code]
        """
        self.pre_event(requested_version, self.events, event)
        code = ""
        current_required_contexts = []
        if not isinstance(procedure, list):
            log(
                FATAL,
                "Procedure is not list but instead of type %s (%s)"
                % (type(procedure), procedure),
            )
        for block in procedure:
            returned = self.handle_block(block, requested_version, self.blocks)
            code += returned["file_contents"]
            current_required_contexts.extend(returned["required_contexts"])
            self.required_imports.extend(returned["required_imports"])

        current_required_contexts.extend(self.required_contexts)
        custom_contexts: dict[str, str] = {}
        while current_required_contexts != []:
            current_required_contexts = [
                x for x in current_required_contexts if x not in self.current_contexts
            ]
            for rc in current_required_contexts:
                for gc in self.contexts:
                    if gc["name"] == rc:
                        custom_contexts.update(
                            {
                                rc: get_file_contents(
                                    gc["version_instance"][requested_version]["file"]
                                )
                            }
                        )
                        self.current_contexts.append(rc)
                        self.required_imports.extend(
                            gc["version_instance"][requested_version][
                                "required_imports"
                            ]
                        )
                        current_required_contexts.extend(
                            gc["version_instance"][requested_version][
                                "required_contexts"
                            ]
                        )
                        break
                else:
                    log(
                        FATAL,
                        f"Unable to find a context with the name '{rc}' in/for %s"
                        % event,
                    )

        final_code = replace(
            self.event_code,
            {"code": code},
        )

        return final_code, custom_contexts, list(set(self.required_imports))
