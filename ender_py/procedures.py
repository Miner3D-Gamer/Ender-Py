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
    searched: Optional[Type[T]] = None,
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


class Block(TypedDict):
    # type: str
    name: str
    file: dict[str, str]
    required_imports: list[str]
    required_contexts: list[str]
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
    file: dict[str, str]
    required_imports: list[str]
    given_contexts: list[str]


class Context(TypedDict):
    name: str
    file: dict[str, str]
    required_imports: list[str]
    required_contexts: list[str]


def get_full_file_paths(procedure_blocks_path: str, folder: str, yep):
    new = {}
    for key, value in yep.items():
        new[key] = jp(os.getcwd(), procedure_blocks_path, folder, value)
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
                        name=get(block, "name", searched=str),
                        file=get_full_file_paths(
                            procedure_blocks_path,
                            folder,
                            get(block, "file", block["name"], searched=dict[str, str]),
                        ),
                        required_imports=get(
                            block,
                            "required_imports",
                            [],
                            block["name"],
                            searched=list[str],
                        ),
                        given_contexts=get(
                            block,
                            "given_contexts",
                            [],
                            block["name"],
                            searched=list[str],
                        ),
                    )
                    self.events.append(new)
                elif block["type"] == "context":
                    new = Context(
                        name=get(block, "name", searched=str),
                        file=get_full_file_paths(
                            procedure_blocks_path,
                            folder,
                            get(block, "file", block["name"], searched=dict[str, str]),
                        ),
                        required_imports=get(
                            block,
                            "required_imports",
                            [],
                            block["name"],
                            searched=list[str],
                        ),
                        required_contexts=get(
                            block,
                            "required_contexts",
                            [],
                            block["name"],
                            searched=list[str],
                        ),
                    )
                    self.contexts.append(new)
                else:
                    new = Block(
                        name=get(block, "name", searched=str),
                        required_imports=get(
                            block,
                            "required_imports",
                            [],
                            block["name"],
                            searched=list[str],
                        ),
                        required_contexts=get(
                            block,
                            "required_contexts",
                            [],
                            block["name"],
                            searched=list[str],
                        ),
                        file=get_full_file_paths(
                            procedure_blocks_path,
                            folder,
                            get(block, "file", block["name"], searched=dict[str, str]),
                        ),
                        output=get(
                            block, "output", "none", block["name"], searched=str
                        ),
                        inputs=get(
                            block,
                            "inputs",
                            [],
                            block["name"],
                            searched=list[dict[str, str]],
                        ),
                    )
                    # new = {
                    #     "name": get(block, "name"),
                    #     "required_imports": get(block, "required_imports", [], block["name"]),
                    #     "required_contexts": get(block, "required_contexts", [], block["name"]),
                    #     "file": get(block, "file", block["name"]),
                    #     "output": get(block, "output", "none", block["name"]),
                    #     "inputs": get(block, "inputs", [], block["name"])
                    # }

                    self.blocks.append(new)

    def pre_event(
        self,
        requested_version: str,
        events: list[Event],
        event: str,
    ):
        self.current_contexts: list[str] = []
        self.required_imports: list[str] = []
        if event == "none":
            self.event_code = "{imports}\npublic static void none(){{code}}"
        else:
            for i in events:
                if i["name"] == event:
                    self.required_imports.extend(i["required_imports"])
                    self.current_contexts.extend(i["given_contexts"])
                    self.event_code = get_file_contents(i["file"][requested_version])
                    break
            else:
                log(FATAL, f"Event {event} not found")

    def does_throughput_match(self, lower: dict, higher: dict):
        return lower["type"] == higher["output"]

    def handle_block(
        self,
        block: dict[str, Any],
        requested_version: str,
        blocks: list[Block],
    ) -> Union[NoReturn, dict]:
        for b in blocks:
            if b["name"] == block["action"]:
                inputs = b["inputs"]
                contents = get_file_contents(b["file"][requested_version])
                self.required_imports.extend(b["required_imports"])
                if inputs == []:
                    return {
                        "required_imports": b["required_imports"],
                        "required_contexts": b["required_contexts"],
                        "file_contents": contents,
                        "output": b["output"],
                    }
                for singular_expected_input in inputs:
                    type = singular_expected_input["type"]
                    if type == "literal":
                        allowed = singular_expected_input["expected"]
                        if isinstance(allowed, dict):
                            inp = block[singular_expected_input["name"]]
                            if inp not in allowed:
                                log(
                                    FATAL,
                                    f"Expected one of {[x for x in allowed]} but got {inp} in block {block['action']}",
                                )
                            given = {
                                "file_contents": allowed[inp],
                                "required_imports": b["required_imports"],
                                "required_contexts": b["required_contexts"],
                            }
                        elif isinstance(allowed, list):
                            ...
                        elif isinstance(allowed, str):
                            if allowed == "str":
                                if isinstance(
                                    block[singular_expected_input["name"]], str
                                ):
                                    given = {
                                        "file_contents": f'"{block[singular_expected_input["name"]]}"',
                                        "required_imports": b["required_imports"],
                                        "required_contexts": b["required_contexts"],
                                    }
                                else:
                                    log(
                                        FATAL,
                                        f"Expected a string but got {block[singular_expected_input['name']]} in block {block['action']}",
                                    )
                            else:
                                log(FATAL, "Expected allowed to be str")
                        else:
                            log(
                                FATAL,
                                "Expected 'literal' to be a string, dict, or list",
                            )
                    else:
                        next = block.get(singular_expected_input["name"])
                        if next is None:
                            log(
                                FATAL,
                                f"Input '{singular_expected_input['name']}' not found in block '{block['action']}' (Procedure)",
                            )
                        if isinstance(next, list):
                            sub_contents = ""
                            further_required_imports = []
                            further_required_contexts = []
                            for n in next:
                                next_given = self.handle_block(
                                    n, requested_version, blocks
                                )
                                # Limit what is allowed to be passed between a hugging block and its insides
                                # if not self.does_throughput_match(
                                #     singular_expected_input, next_given
                                # ):
                                #     log(
                                #         FATAL,
                                #         f"Expected throughput '{singular_expected_input['type']}' but got throughput '{next_given['output']}' between blocks '{block['action']}' and '{n['action']}' (Hugging action list)",
                                #     )
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
                            }
                        elif isinstance(next, str):
                            given = {
                                "file_contents": next,
                                "required_imports": b["required_imports"],
                                "required_contexts": b["required_contexts"],
                            }
                        else:
                            given = self.handle_block(next, requested_version, blocks)
                            if not self.does_throughput_match(
                                singular_expected_input, given
                            ):
                                log(
                                    FATAL,
                                    f"Expected throughput '{singular_expected_input['type']}' but got throughput '{given['output']}' between blocks '{block['action']}' and '{next['action']}'",
                                )
                    contents = replace(
                        contents,
                        {singular_expected_input["name"]: given["file_contents"]},
                    )
                # print(b["required_imports"]
                #    + given["required_imports"])
                return {
                    "required_imports": b["required_imports"]
                    + given["required_imports"],
                    "required_contexts": b["required_contexts"]
                    + given["required_contexts"],
                    "file_contents": contents,
                    "output": b["output"],
                }
        log(FATAL, f"Block {block} not found")

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

        custom_contexts: dict[str, str] = {}
        while current_required_contexts != []:
            current_required_contexts = [
                x for x in current_required_contexts if x not in self.current_contexts
            ]
            for rc in current_required_contexts:
                for gc in self.contexts:
                    if gc["name"] == rc:
                        custom_contexts.update(
                            {rc: get_file_contents(gc["file"][requested_version])}
                        )
                        self.current_contexts.append(rc)
                        self.required_imports.extend(gc["required_imports"])
                        current_required_contexts.extend(gc["required_contexts"])
                        break
                else:
                    log(FATAL, f"Unable to find a context with the name '{rc}'")

        final_code = replace(
            self.event_code,
            {"code": code},
        )

        return final_code, custom_contexts, list(set(self.required_imports))
