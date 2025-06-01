from typing import Optional, Any, TypedDict, Callable, cast, overload, Literal, Union

import shared.base
from .bundler import generate_blocks, handle_bundler
from . import components

from concurrent.futures import ThreadPoolExecutor
import json
import shutil
import time
from functools import wraps


from .components import (
    COMPONENT_TYPE,
    Block,
    Item,
    CreativeTab,
    LootTable,
    Procedure,
    Recipe,
    Unused,
    Tag,
    TagManager,
    Model,
    # RecipeCrafting,
    # RecipeItemTag,
    # RecipeCraftingShapeless,
)
from .fast_io import fast_copytree
from .internal_shared import (
    jp,
    replace,
    add_mod_id_if_missing,
    is_valid_url,
    dynamic_serializer,
)
from . import internal_shared
from .one_off_functions import (
    import_module_from_full_path,
    performance_handler,
    print_performance,
    performance_add_end_marker,
)
from shared import log, FATAL, WARN, INFO, ERROR  # , image_compression

from .procedures import ProcedureInternal

from fast_functions import *

from .mod_helper import *


from .internal_shared import (
    export_class,
    import_class,
)


import importlib.util

from . import this

common_cache = jp(this, "cache")


def is_library_installed(library_name: str) -> bool:
    spec = importlib.util.find_spec(library_name)
    return spec is not None


if is_library_installed("tge"):
    import tge

    profile = tge.tbe.profile
else:

    def do_nothing(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    profile = do_nothing


class SortedComponents(TypedDict):
    item_textures: list[str]
    item_models: list[Model]
    block_textures: list[dict[str, str]]
    block_models: list[Model]
    language: dict[str, str]
    items: dict[str, Item]
    blocks: dict[str, Block]
    creative_tabs: dict[str, CreativeTab]
    internal_loot_tables: list[LootTable]
    tags: list[Tag]

    procedures: dict[str, Procedure]
    recipes: dict[str, Recipe]


class ModInfo(TypedDict):
    internal_id: str
    id: str
    minecraft_version: str
    mod_loader_version: str
    mod_loader: str


class Mod:
    __slots__ = [
        "internal_id",
        "id",
        "name",
        "author",
        "description",
        "version",
        "license",
        "available",
        "components",
        "unordered_components",
        "external_packs",
        "homepage",
        "minify",
        "mdk_paths",
    ]

    def __init__(
        self,
        internal_id: str,
        public_id: str,
        name: str,
        author: str,
        description: str,
        version: str,
        license: str,
        mdk_parent_folder: str,
        external_packs: list[str] = [],
        homepage: str = "",
    ) -> None:
        if not is_valid_internal_mod_id(internal_id):
            raise Exception("Invalid internal mod id")
        self.internal_id = internal_id
        self.id = public_id
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.license = license
        self.external_packs = external_packs
        self.homepage = homepage
        if homepage != "" and not is_valid_url(homepage):
            log(WARN, f"Homepage {homepage} is not a valid url")

        self.components: dict[str, COMPONENT_TYPE] = {}
        self.unordered_components: list[COMPONENT_TYPE] = []
        # self.tags: dict[str, dict[str, list[str]]] = {"minecraft": {}}
        # tools = ["axe", "pickaxe", "shovel", "hoe"]

        # for tool in tools:
        #     self.tags["minecraft"]["blocks/mineable/" + tool] = []

        self.available: list[str] = []
        self.mdk_paths = mdk_parent_folder

        for root, _folders, files in os.walk(mdk_parent_folder):

            if not root.startswith(mdk_parent_folder):
                continue

            for file in files:
                if file == "gradle.properties":
                    for v in self.available:
                        if root.startswith(v):
                            continue
                    # get name of deepest foler
                    f = os.path.normpath(root).split("\\")[-1]
                    if f.__contains__("-"):
                        self.available.append(root)
        if len(self.available) == 0:
            log(FATAL, "No available mdk (compilers) found in %s" % mdk_parent_folder)

        blacklist_file = jp(os.path.dirname(__file__), "blacklist.json")
        if os.path.exists(blacklist_file):
            mod_id_blacklist = json.loads(get_file_contents(blacklist_file))

            for id in mod_id_blacklist["blacklisted"]:
                message = None
                level = -1
                type = id["type"]
                if type == "literal":
                    if self.id == id["value"]:
                        message = id["message"]
                        level: int = getattr(internal_shared, id["level"])
                    else:
                        return
                elif type == "regex":
                    ...
                else:
                    return
                if not message:
                    log(FATAL, "Invalid blacklist message type")
                if message["type"] == "literal":
                    msg = message["value"]
                elif message["type"] == "template":
                    msg = mod_id_blacklist["messages"][message["value"]]
                else:
                    log(FATAL, "Invalid message type")

                log(level, msg)
            # if self.id in mod_id_blacklist["blacklisted"]:
            #     log(FATAL, f"Blacklisted mod id {self.id}")

    @overload
    def export(
        self, indent: Literal[-1] = -1, include_external_packs: bool = False
    ) -> dict[str, Any]: ...

    @overload
    def export(self, indent: int, include_external_packs: bool = False) -> str: ...

    def export(
        self, indent: int = -1, include_external_packs: bool = False
    ) -> dict[str, Any] | str:
        if indent >= 0:
            return json.dumps(
                export_mod(self, include_external_packs),
                indent=indent,
                default=dynamic_serializer,
                ensure_ascii=False,
            )
        return export_mod(self, include_external_packs)

    @classmethod
    def import_mod(
        cls,
        data: dict[str, Any] | str,
        mdk_folder: str,
        external_packs: Optional[list[str]] = None,
    ) -> "Mod":
        "The word 'import' is a python keyword so we have to call this function something stupid."
        return import_mod(data, mdk_folder, external_packs)

    def add_component(
        self,
        *,
        component: COMPONENT_TYPE,
        id: Optional[str],
        do_not_replace: Optional[bool] = None,
    ):
        """
        do_not_replace:
            True: will error when trying to add component with same id
            False: will replace component
            None:  will replace component yet give an ERROR warning
        """
        if component.TYPE in ["loot_table", "tag"]:
            self.unordered_components.append(component)
        if id is None:
            log(FATAL, "No id provided for component")
        elif not is_valid_component_id(id):
            log(FATAL, f"Invalid component id: '{id}'")

        if self.components.__contains__(id):
            if do_not_replace is True:
                log(
                    FATAL,
                    f"Component with id '{id}' already exists -> trying to replace {self.components[id].TYPE} with {component.TYPE}",
                )
            elif do_not_replace is False:
                pass
            else:
                log(
                    WARN,
                    f"Component with id '{id}' already exists -> replacing {self.components[id].TYPE} with {component.TYPE}",
                )

        self.components[id] = component

    def add_components(
        self,
        items: dict[str | Any, COMPONENT_TYPE],
        do_not_replace: Optional[bool] = None,
    ):
        for id, component in items.items():
            self.add_component(
                component=component, id=id, do_not_replace=do_not_replace
            )

    def remove_component(self, id: str):
        del self.components[id]

    def remove_components(self, ids: list[str]):
        for id in ids:
            del self.components[id]

    def get_components(self, ids: list[str]):
        return [self.components[id] for id in ids]

    def get_component(self, id: str):
        return self.components[id]

    def __repr__(self) -> str:
        a = len(self.unordered_components) + len(self.components)
        info: dict[str, Union[str, int]] = {
            "internal_id": self.internal_id,
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "version": self.version,
            "license": self.license,
            "component_amount": a,
        }
        insert = "%s=%s"
        sep = ", "
        encompassing = "Mod(%s)"

        return_value = encompassing % sep.join(
            insert % (k, repr(v)) for k, v in info.items()
        )
        return return_value

    def get_sorted_components(self) -> SortedComponents:
        sorted = SortedComponents(
            item_textures=[],
            item_models=[],
            block_textures=[],
            block_models=[],
            language={},
            items={},
            blocks={},
            creative_tabs={},
            internal_loot_tables=[],
            procedures={},
            recipes={},
            tags=[],
        )
        for component_id, component in self.components.items():
            if isinstance(component, Item):
                sorted["item_textures"].append(component.texture)
                sorted["item_models"].append(Model(component_id, None, True))
                sorted["items"].update({component_id: component})
            elif isinstance(component, CreativeTab):
                sorted["creative_tabs"].update({component_id: component})
            elif isinstance(component, Block):
                sorted["block_textures"].append(component.texture)
                sorted["block_models"].append(Model(component_id, None))
                sorted["blocks"].update({component_id: component})
            elif isinstance(component, Procedure):
                sorted["procedures"].update({component_id: component})
            elif isinstance(component, Recipe):
                sorted["recipes"].update({component_id: component})
            else:
                raise Exception("Unknown component type '%s" % type(component))

        for component in self.unordered_components:
            if isinstance(component, Tag):
                sorted["tags"].append(component)
            elif isinstance(component, LootTable):
                sorted["internal_loot_tables"].append(component)
            else:
                raise Exception("Unknown unsorted component type '%s" % type(component))

        return sorted

    @profile
    def generate(
        self,
        minify: bool = True,
        multithreading: bool = True,
        _language_update_file: Unused = None,
    ) -> None:

        self.minify = minify

        actions = self.get_sorted_components()

        # log(DEBUG, "Cleaning Cache")
        fast_rmtree(common_cache)

        # log(DEBUG, "Iterating through available paths")
        if multithreading:
            with ThreadPoolExecutor() as executor:
                executor.map(
                    self.safe_generate_mod_for_path,
                    self.available,
                    [actions] * len(self.available),  # There has got to be a better way
                )
        else:
            for path in self.available:
                # Adding the try except doubled the generation time - Not gud :(
                self.safe_generate_mod_for_path(path, actions)
        print_performance()

    def safe_generate_mod_for_path(self, path: str, actions: SortedComponents):
        try:
            return self.generate_mod_for_path(path, actions)
        except SystemExit:
            pass
        except BaseException as e:
            print("An error occured while generating...")
            print(e)
        return None

    def generate_mod_for_path(self, mdk_path: str, actions: SortedComponents):
        start = time.perf_counter()
        things_added: list[str] = (
            []
        )  # Document what got added so no unncessary bundlers are inserted in the entry point file

        def get_info_from_path(path: str):
            info: list[str] = path.replace("\\", "/").split("/")[-1].split("-")

            match len(info):
                case 1:
                    raise Exception(
                        "Invalid mod path (Expected file of {mod_loader}-{minecraft_version}-{mod_loader_version} but got '%s'): %s"
                        % (info, path)
                    )
                case 2:
                    mod_loader, minecraft_version = info
                    mod_loader_version = ""
                case 3:
                    mod_loader, minecraft_version, mod_loader_version = info
                case _:
                    mod_loader, minecraft_version, mod_loader_version, *_ = info
            assert isinstance(mod_loader, str)
            assert isinstance(minecraft_version, str)
            assert isinstance(mod_loader_version, str)
            return mod_loader, minecraft_version, mod_loader_version

        mod_loader_, minecraft_version_, mod_loader_version_ = get_info_from_path(
            mdk_path
        )

        mod_info = ModInfo(
            internal_id=self.internal_id,
            id=self.id,
            minecraft_version=minecraft_version_,
            mod_loader_version=mod_loader_version_,
            mod_loader=mod_loader_,
        )

        triple_trouble = [
            mod_info["mod_loader"],
            mod_info["minecraft_version"],
            mod_info["mod_loader_version"],
        ]
        skip_message = f"skipping " + " ".join(triple_trouble)
        unique_name = "_".join(triple_trouble)

        replace_files = os.path.join(
            this,
            mod_info["mod_loader"],
            mod_info["minecraft_version"],
            mod_info["mod_loader_version"],
        )
        if mod_info["mod_loader_version"]:  # not os.path.exists(replace_files):
            replace_files = os.path.join(
                this, mod_info["mod_loader"], mod_info["minecraft_version"]
            )
            log(
                INFO,
                "Now generating for %s %s"
                % (mod_info["mod_loader"].title(), mod_info["minecraft_version"]),
            )
        else:
            log(
                INFO,
                "Now generating for %s %s (%s)"
                % (
                    mod_info["mod_loader"].title(),
                    mod_info["minecraft_version"],
                    mod_info["mod_loader_version"],
                ),
            )

        default_path = jp(this, "defaults")
        performance_handler(unique_name, "Init", "Figuring out version", start)

        performance_handler(
            unique_name, "Plugin setup", "Setting up Configurator", None
        )

        ##### GENERATING DATAPACK/RESOURCEPACK MOD THINGS
        configurator_path = jp(replace_files, "configurator.py")
        if not os.path.exists(configurator_path):
            log(
                FATAL,
                f"{unique_name} Configurator at {configurator_path} does not exist, skipping {mod_info['mod_loader']} {mod_info['minecraft_version']} {mod_info['mod_loader_version']}",
            )

        def apply_configurator_to_dict(
            configurator_path: str, configurator: dict[str, Callable[..., Any]]
        ):
            for key, value in import_module_from_full_path(
                configurator_path
            ).__dict__.items():
                if key.startswith("__"):
                    continue
                configurator[key] = value
            return configurator

        configurator: dict[str, Callable[..., Any]] = {}
        configurator = apply_configurator_to_dict(configurator_path, configurator)
        configurator = apply_configurator_to_dict(
            jp(default_path, "configurator.py"), configurator
        )

        final_cache_path = jp(common_cache, unique_name, "final")
        template_cache_path = jp(common_cache, unique_name, "template")

        code_java_cache_path = os.path.join(final_cache_path, "code", "java")

        pack_path = os.path.join(final_cache_path, "packs")
        resource_pack_path = os.path.join(pack_path, "assets", self.id)
        data_pack_path = os.path.join(pack_path, "data")

        ###

        info_path = jp(
            replace_files, "info.json"
        )  # This says what minecraft versions it supports
        if not os.path.exists(info_path):
            log(
                FATAL,
                f"{unique_name} Info path {info_path} does not exist, {skip_message}",
            )

        info_replace = json.loads(get_file_contents(info_path))

        ###

        resource_path = jp(replace_files, "things", "resources")
        if not os.path.exists(resource_path):
            resource_path = jp(default_path, "resources")
            # log(ERROR, f"Resource path {resource_path} does not exist, skipping {mod_loader} {minecraft_version} {mod_loader_version}")
            # continue

        performance_handler(
            unique_name,
            "Header",
            "Assembling cache data/resource packs (%s)" % len(self.external_packs),
            None,
        )
        del final_cache_path

        assemble_pack(
            resource_path,
            template_cache_path,
            pack_path,
            self.id,
            self,
            mod_info,
            info_replace,
        )

        performance_handler(
            unique_name,
            "Header",
            "Merging given resources into cache (%s)" % len(self.external_packs),
            None,
        )
        del resource_path
        print("|>", self.external_packs)
        for pack in self.external_packs:
            copy_and_rename_builtin(pack, template_cache_path, self.id)

        performance_handler(
            unique_name, "Header", "Setting up datapack/resourcepack", None
        )

        mdk_src_main = os.path.join(mdk_path, "src/main")
        java_path = os.path.join(
            mdk_src_main, "java/" + self.internal_id.replace(".", "/")
        )
        resource_path = os.path.join(mdk_src_main, "resources/")

        ### Actual Mod stuff
        if not os.path.exists(code_java_cache_path):
            os.makedirs(code_java_cache_path)

        tag_manager = TagManager()

        block_amount = len(actions["blocks"])
        if block_amount == 0:
            pass
            # performance_handler(unique_name, "Blocks", "Skipping blocks", None)
        else:
            things_added.append("blocks")
            performance_handler(
                unique_name,
                "Blocks",
                "Generating code (%s)" % block_amount,
                None,
            )
            map_color_path = jp(replace_files, "blocks/map_colors.json")
            if not os.path.exists(map_color_path):
                log(
                    WARN,
                    f"{unique_name} Block color path not found/not supported (%s)"
                    % map_color_path,
                )
                map_color_path = None

            fallback_path = jp(
                default_path,
                "resources",
                "assets",
                "builtin",
                "textures",
                "blocks",
                "error.png",
            )
            block_items, block_loot_tables, block_translations = generate_blocks(
                actions["blocks"],
                self,
                template_cache_path,
                replace_files,
                configurator,
                code_java_cache_path,
                map_color_path,
                fallback_path,
                tag_manager,
                unique_name,
                mod_info,
                info_replace,
            )
            actions["items"].update(block_items)
            actions["internal_loot_tables"].extend(block_loot_tables)
            actions["language"].update(block_translations)
            del (
                block_items,
                block_loot_tables,
                block_translations,
                fallback_path,
                map_color_path,
            )

        # ITEMS

        item_amount = len(actions["items"])
        if item_amount == 0:
            # performance_handler(unique_name, "Items", "Skipping items", None)
            pass
        else:
            performance_handler(
                unique_name,
                "Items",
                "Generating code (Bundler) (%s)" % item_amount,
                None,
            )
            item_bundler, item_files, translation_keys = handle_bundler(
                {
                    "bundler": jp(replace_files, "items/item_bundler.java"),
                    "import": jp(replace_files, "items/import_line.java"),
                    "code": jp(replace_files, "items/item_code.java"),
                    "component": jp(replace_files, "items/item_component.java"),
                    "properties": jp(replace_files, "items/properties.json"),
                },
                self,
                actions["items"],
                configurator,
                self.minify,
            )

            actions["language"].update(translation_keys)
            performance_handler(unique_name, "Items", "Writing code to cache", None)

            write_to_file(jp(code_java_cache_path, "ModItems.java"), item_bundler)
            things_added.append("items")

            for file, code in item_files.items():
                write_to_file(jp(code_java_cache_path, f"items/{file}.java"), code)

            del item_bundler, item_files, translation_keys

        cerative_tab_amount = len(actions["creative_tabs"])
        if cerative_tab_amount == 0:
            pass
        else:
            performance_handler(
                unique_name,
                "Items",
                "Generating code (Bundler) (%s)" % cerative_tab_amount,
                None,
            )
            creative_tab_bundler, creative_tab_files, translation_keys = handle_bundler(
                {
                    "bundler": jp(
                        replace_files,
                        "creative_tabs/creative_tab_bundler.java",
                    ),
                    "import": jp(replace_files, "creative_tabs/import_line.java"),
                    "code": jp(
                        replace_files,
                        "creative_tabs/creative_tab_code.java",
                    ),
                    "component": jp(
                        replace_files,
                        "creative_tabs/creative_tab_component.java",
                    ),
                    "item": jp(
                        replace_files,
                        "creative_tabs/creative_tab_item.java",
                    ),
                    "properties": jp(replace_files, "creative_tabs/properties.json"),
                },
                self,
                actions["creative_tabs"],
                configurator,
                self.minify,
            )

            actions["language"].update(translation_keys)
            performance_handler(
                unique_name, "Creative Tabs", "Writing code to cache", None
            )

            with open(jp(code_java_cache_path, "ModCreativeModeTabs.java"), "w") as f:
                f.write(creative_tab_bundler)
            things_added.append("creative_mode_tabs")

            for file, code in creative_tab_files.items():
                write_to_file(
                    jp(code_java_cache_path, f"creative_tabs/{file}.java"), code
                )

            del creative_tab_bundler, creative_tab_files, translation_keys

        procedure_amount = len(actions["procedures"])
        if procedure_amount == 0:
            pass
        else:
            performance_handler(
                unique_name, "Procedures", "Generating (%s)" % procedure_amount, None
            )
            event_wrapper_location = jp(replace_files, "procedures/event_handler.java")
            if not os.path.exists(event_wrapper_location):
                log(
                    FATAL,
                    f"{unique_name} Unable to find event wrapper at '%s', %s"
                    % (event_wrapper_location, skip_message),
                )
            total_code = ""
            total_contexts: dict[str, str] = {}
            total_imports: list[str] = []
            for procedure_id, procedure in actions["procedures"].items():
                procedure: Procedure
                if procedure.event:
                    new = ProcedureInternal()
                    new.load_blocks(jp(os.path.dirname(__file__), "procedures"))
                    code, contexts, imports = new.handle_event(
                        procedure.content,
                        "%s-%s"
                        % (
                            mod_info["mod_loader"],
                            mod_info["minecraft_version"],
                        ),  # Improve this
                        procedure.event,
                    )
                    total_code += "\n" + code
                    total_imports.extend(imports)
                    total_contexts.update(contexts)
                else:
                    log(
                        WARN,
                        f"{unique_name} Procedure %s has no event, %s"
                        % (procedure_id, skip_message),
                    )

            total_imports = list(set(total_imports))
            event_wrapper = get_file_contents(event_wrapper_location)
            event_wrapper = format_text(
                event_wrapper,
                self,
                mod_info,
                {
                    "imports": "\n".join(["import %s;" % x for x in total_imports]),
                    "events": total_code,
                    "contexts": "\n".join(total_contexts.values()),
                },
            )
            performance_handler(unique_name, "Procedures", "Writing to file", None)

            write_to_file(jp(code_java_cache_path, "EventHandler.java"), event_wrapper)

            things_added.append("procedures")

            del event_wrapper, total_code, total_imports, total_contexts

        performance_handler(unique_name, "Translation", "Writing to file", None)
        ### Translations

        translation_path = jp(resource_pack_path, "lang/en_us.json")
        os.makedirs(os.path.dirname(translation_path), exist_ok=True)
        with open(translation_path, "w") as f:
            json.dump(actions["language"], f, indent=4)

        performance_handler(unique_name, "Models", "Setting up", None)

        ### Textures + Models
        class RquiredTexture(TypedDict):
            item: set[str]
            block: set[str]

        required_textures = RquiredTexture(
            item=set(),
            block=set(),
        )

        # Block models/blockstates
        block_model_path = jp(resource_pack_path, "models/block")
        if not os.path.exists(block_model_path):
            os.makedirs(block_model_path)
        blockstate_model_path = jp(pack_path, "assets", self.id, "blockstates")
        if not os.path.exists(blockstate_model_path):
            os.makedirs(blockstate_model_path)

        block_state_path_template = jp(
            template_cache_path, "assets", self.id, "blockstates"
        )

        block_states = {
            "none": jp(block_state_path_template, "cube.json"),
            "falling": jp(block_state_path_template, "cube.json"),
            "slab": jp(block_state_path_template, "slab.json"),
            "stair": jp(block_state_path_template, "stairs.json"),
            "fence": jp(block_state_path_template, "fence.json"),
            "fence_gate": jp(block_state_path_template, "fence_gate.json"),
            "door": jp(block_state_path_template, "door.json"),
            "trap_door": jp(block_state_path_template, "trap_door.json"),
            "button": jp(block_state_path_template, "button.json"),
            "leaves": jp(block_state_path_template, "cube.json"),
            "pressure_plate": jp(block_state_path_template, "pressure_plate.json"),
            "log": jp(block_state_path_template, "log.json"),
            "wall": jp(block_state_path_template, "wall.json"),
        }
        performance_handler(
            unique_name,
            "Models",
            "Generating Block Models and blockstates (%s)" % len(actions["blocks"]),
            None,
        )
        block_state_jobs_paths: list[str] = []
        block_state_jobs_contents: list[str] = []
        block_state_jobs_length = 0

        block_model_jobs_paths: list[str] = []
        block_model_jobs_contents: list[str] = []
        block_model_jobs_length = 0

        for block_id, block in actions["blocks"].items():
            block_id: str
            block: Block

            # Block state

            blockstate_path_for_this_block = jp(
                template_cache_path,
                "assets",
                self.id,
                "blockstates",
                (
                    block_states[block.rotation]
                    if block.blocktype == "cube"
                    else block_states[block.blocktype]
                ),
            )
            blockstate_data = replace(
                get_file_contents(blockstate_path_for_this_block),
                {"mod_id": self.id, "block_id": block_id},
            )

            blockstate_path = jp(blockstate_model_path, f"{block_id}.json")

            block_state_jobs_paths.append(blockstate_path)
            block_state_jobs_contents.append(blockstate_data)
            block_state_jobs_length += 1

            # BLOCK STATE DONE

            all_models = get_all_models_in_blockstate(
                get_file_contents(blockstate_path_for_this_block)
            )
            # Models

            for model in set(all_models):
                model_path = (
                    jp(
                        template_cache_path,
                        "assets",
                        model.replace(
                            "{mod_id}:block/{block_id}",
                            f"{self.id}/models/block/{block.blocktype}",
                        ),
                    )
                    + ".json"
                )
                if not os.path.exists(model_path):
                    old = model_path
                    model_path = (
                        jp(
                            template_cache_path,
                            "assets",
                            model.replace(
                                "{mod_id}:block/{block_id}",
                                f"{self.id}/models/block/cube",
                            ),
                        )
                        + ".json"
                    )
                    if not os.path.exists(model_path):
                        log(
                            FATAL,
                            f"{unique_name} Unable to find suitable model for block {self.id}, tried following paths: \n>{old}\n>{model_path}",
                        )

                model_data = get_file_contents(model_path)
                model_data = replace(model_data, block.texture)
                model_data = replace(
                    model_data,
                    {"mod_id": self.id},
                )
                for key, val in block.texture.items():
                    if key == "render_type":
                        continue
                    required_textures["block"].add(val.split("/")[-1])

                model_name_path_extension = model.replace(
                    "{mod_id}:block/{block_id}",
                    "",
                )
                model_path = jp(
                    block_model_path, f"{block_id}{model_name_path_extension}.json"
                )
                block_model_jobs_paths.append(model_path)
                block_model_jobs_contents.append(model_data)
                block_model_jobs_length += 1
        performance_handler(
            unique_name,
            "Models",
            "Writing block models to cache (%s)" % block_model_jobs_length,
            None,
        )
        write_to_files(
            block_model_jobs_paths, block_model_jobs_contents, block_model_jobs_length
        )

        # for block_model_path, block_model_data in block_model_jobs:
        #     with open(block_model_path, "w") as f:
        #         f.write(block_model_data)

        performance_handler(
            unique_name,
            "Models",
            "Generating (Block) Item Models (%s)" % len(actions["items"]),
            None,
        )
        # Item models

        item_model_path = jp(resource_pack_path, "models/item")
        item_model_job_paths: list[str] = []
        item_model_job_contents: list[str] = []
        item_model_job_length = 0

        for item_id, item in actions["items"].items():
            item_id: str
            item: Item
            temp = item.display_item.split(";", 1)
            if len(temp) == 1:
                display_item_mod_id, display_item_texture = (
                    self.id,
                    item.texture,
                )
                display_type = temp[0]
            else:
                display_type, rest = temp
                if ":" in rest:
                    display_item_mod_id, display_item_texture = rest.split(":", 1)
                else:
                    display_item_mod_id = self.id
                    display_item_texture = rest

            match display_type:
                case "block":
                    item_model = jp(
                        template_cache_path,
                        "assets",
                        f"{self.id}/models/block/{item.block_item_type}_item.json",
                    )
                    if not os.path.exists(item_model):
                        item_model = jp(
                            template_cache_path,
                            "assets",
                            f"{self.id}/models/block/cube_item.json",
                        )
                    parent = json.loads(get_file_contents(item_model)).get("parent")

                    if parent:
                        ### ARE YOU SURE THIS WILL WORK?
                        # I HAVE NO IDEA

                        # HAHA NOPE IT DOES NOT
                        block_model_output_path = replace(
                            parent,
                            {
                                "mod_id": display_item_mod_id,
                                "block_id": display_item_texture,
                            },
                        ).replace(":", "/models/")
                        block_model_output_path = (
                            jp(pack_path, "assets", block_model_output_path) + ".json"
                        )
                        if not os.path.exists(block_model_output_path):
                            if item.block_item_type is None:
                                log(
                                    FATAL,
                                    f"{unique_name} Block item type is None for block item",
                                )

                            block_model_input_path = replace(
                                parent,
                                {
                                    "mod_id": self.id,
                                    "block_id": item.block_item_type,
                                },
                            ).replace(":", "/models/")

                            model_path = (
                                jp(
                                    template_cache_path,
                                    "assets",
                                    block_model_input_path,
                                )
                                + ".json"
                            )
                            if not os.path.exists(model_path):
                                model_path = (
                                    jp(
                                        template_cache_path,
                                        "assets",
                                        os.path.dirname(block_model_input_path),
                                        "cube",
                                    )
                                    + ".json"
                                )
                                if not os.path.exists(model_path):
                                    log(
                                        FATAL,
                                        f"{unique_name} Cannot get item model path :(",
                                    )
                                else:
                                    log(
                                        WARN,
                                        f"{unique_name} Unable to find item model for %s, using default cube instead"
                                        % item_id,
                                    )

                            item_model_data = replace(
                                get_file_contents(
                                    model_path,
                                    info="Getting item model",
                                ),
                                combine_dicts(item.block_item_textures, {"mod_id": display_item_mod_id}),  # type: ignore
                            )
                            item_model_job_paths.append(block_model_output_path)
                            item_model_job_contents.append(item_model_data)
                            item_model_job_length += 1

                    if not os.path.exists(item_model):
                        item_model = jp(
                            template_cache_path,
                            "assets",
                            f"{self.id}/models/block/cube_item.json",
                        )
                case "item":
                    item_model = jp(
                        template_cache_path,
                        "assets",
                        f"{self.id}/models/item/items.json",
                    )
                    required_textures["item"].add(item.texture)
                case _:
                    log(FATAL, f"{unique_name} Unknown display type {display_type}")

            model_data = replace(
                get_file_contents(item_model),
                (
                    {
                        "texture": item.texture,
                        "mod_id": display_item_mod_id,
                        "block_id": display_item_texture,
                    }
                ),
            )

            model_path = jp(item_model_path, f"{item_id}.json")
            item_model_job_paths.append(model_path)
            item_model_job_contents.append(model_data)
            item_model_job_length += 1
            del model_data, model_path, item

        performance_handler(
            unique_name,
            "Models",
            "Writing (block) item models (%s)" % item_model_job_length,
            None,
        )

        write_to_files(
            item_model_job_paths, item_model_job_contents, item_model_job_length
        )
        del item_model_job_paths, item_model_job_contents, item_model_job_length
        performance_handler(
            unique_name,
            "Blockstates",
            "Writing blockstates generated in models section to cache (%s)"
            % block_state_jobs_length,
            None,
        )

        write_to_files(
            block_state_jobs_paths, block_state_jobs_contents, block_state_jobs_length
        )

        del block_state_jobs_paths, block_state_jobs_contents, block_state_jobs_length

        performance_handler(
            unique_name,
            "Textures",
            "Gathering required textures (%s)"
            % sum(
                [
                    len(cast(list[str], textures))
                    for textures in required_textures.values()
                ]
            ),
            None,
        )
        # write_to_file("./required_textures.json", json.dumps(required_textures))
        texture_job_paths_from: list[str] = []
        texture_job_paths_to: list[str] = []
        texture_job_length = 0

        for dir, textures in required_textures.items():
            textures = cast(list[str], textures)
            for texture in textures:
                texture_path = jp(
                    template_cache_path, "assets", self.id, "textures", dir, texture
                )
                if not os.path.exists(jp(resource_pack_path, "textures", dir)):
                    os.makedirs(jp(resource_pack_path, "textures", dir))

                target_png = jp(texture_path) + ".png"
                if os.path.exists(target_png):
                    png_final_path = jp(
                        resource_pack_path, "textures", dir, texture + ".png"
                    )
                    texture_job_paths_from.append(target_png)
                    texture_job_paths_to.append(png_final_path)
                    texture_job_length += 1

                    mcmeta = jp(texture_path) + ".png.mcmeta"

                    if os.path.exists(mcmeta):
                        texture_job_paths_from.append(mcmeta)
                        texture_job_paths_to.append(
                            jp(
                                resource_pack_path,
                                "textures",
                                dir,
                                texture + ".png.mcmeta",
                            )
                        )
                        texture_job_length += 1
                else:
                    if texture.__contains__(":"):
                        log(
                            INFO,
                            f"{unique_name} Texture {texture} not found. It will be assumed it exists elsewhere undefined.",
                        )
                    else:
                        log(
                            ERROR,
                            f"{unique_name} Texture {texture} not found. ({jp(texture_path) + '.png'})",
                        )

        performance_handler(
            unique_name,
            "Textures",
            "Copying gathered textures (%s)" % texture_job_length,
            None,
        )
        for idx in range(texture_job_length):
            shutil.copyfile(texture_job_paths_from[idx], texture_job_paths_to[idx])

        del (
            texture_job_paths_from,
            texture_job_paths_to,
            texture_job_length,
            required_textures,
        )
        performance_handler(
            unique_name,
            "Loot Tables",
            "Writing Loot Tables to cache (%s)" % len(actions["internal_loot_tables"]),
            None,
        )

        for loot_table in actions["internal_loot_tables"]:
            loot_table: LootTable
            new_loot_table_path = jp(
                data_pack_path,
                loot_table.mod_id,
                "loot_tables",
                loot_table.context,
                f"{loot_table.name}.json",
            )
            if isinstance(loot_table.entries, dict):
                entries = json.dumps(loot_table.entries)
            else:
                entries = loot_table.entries
            write_to_file(new_loot_table_path, entries)

        performance_handler(
            unique_name,
            "Loot Tables",
            "Writing Tags to cache (%s)" % len(tag_manager.tags),
            None,
        )

        for mod_id, values in tag_manager.tags.items():
            if mod_id == "":
                mod_id = self.id
            for path, values in values.items():

                tag_path = jp(data_pack_path, mod_id, "tags", path + ".json")
                thing: dict[str, list[str] | bool] = {
                    "values": [add_mod_id_if_missing(x, self) for x in values],
                    "replace": False,  # Should this be configureable? Yes. Do I know how to properly do that while providing a clean api? No.
                }

                write_to_file(tag_path, json.dumps(thing))

        del tag_manager

        performance_handler(
            unique_name,
            "Recipes",
            "Generating Recipes (%s)" % len(actions["recipes"]),
            None,
        )

        recipes_jobs_paths: list[str] = []
        recipes_jobs_contents: list[str] = []
        recipes_jobs_length = 0

        for key, i in actions["recipes"].items():
            i: Recipe
            new_recipe_path = jp(
                data_pack_path,
                self.id,
                "recipes",
                i.recipe_type,
                f"{key}.json",
            )
            recipe = i.generate(self)
            if recipe:
                recipes_jobs_paths.append(new_recipe_path)
                recipes_jobs_contents.append(recipe)
                recipes_jobs_length += 1

        performance_handler(
            unique_name,
            "Recipes",
            "Writing to cache (%s)" % recipes_jobs_length,
            None,
        )
        write_to_files(recipes_jobs_paths, recipes_jobs_contents, recipes_jobs_length)

        del (
            actions,
            recipes_jobs_paths,
            recipes_jobs_contents,
            recipes_jobs_length,
        )

        ### EVERYTHING IS DONE -> COPY CACHE TO MDK

        performance_handler(unique_name, "Cache", "Clearing MDK", None)
        fast_rmtree(mdk_src_main)

        performance_handler(
            unique_name, "Cache", "Copying cache to MDK (Data/Resource pack)", None
        )
        fast_copytree(pack_path, resource_path)
        performance_handler(
            unique_name, "Cache", "Copying cache to MDK (Java code)", None
        )
        fast_copytree(code_java_cache_path, java_path)

        overwrite_time = time.perf_counter()
        total_overwrites = 0
        # Deal with overwrites
        overwrite_file_path = jp(replace_files, "overwrite.json")
        if os.path.exists(overwrite_file_path):
            overwrite_data = json.loads(get_file_contents(overwrite_file_path))
            total_overwrites = len(overwrite_data)
            for action, overwrites in overwrite_data.items():
                if action == "java_path":
                    action_path = java_path
                elif action == "surface":
                    action_path = mdk_path
                elif action == "resources":
                    action_path = resource_path
                else:
                    log(
                        FATAL,
                        f"{unique_name} Unknown action path '{action}' in {overwrite_file_path}",
                    )
                for overwrite in overwrites:
                    file = jp(replace_files, overwrite["file"])
                    if not os.path.exists(file):
                        log(
                            FATAL, f"{unique_name} Overwrite file {file} does not exist"
                        )
                    offset = overwrite["offset"]
                    file_contents = get_file_contents(file)
                    rename = overwrite.get("rename")

                    if overwrite["format"]:
                        file_contents = format_text(
                            file_contents, self, mod_info, info_replace
                        )

                    write_file_path = jp(
                        action_path,
                        offset,
                        (
                            format_text(rename, self, mod_info, info_replace)
                            if rename
                            else os.path.basename(file)
                        ),
                    )
                    write_to_file(write_file_path, file_contents)

        performance_handler(
            unique_name,
            "Cache",
            "Dealing with overwrite files (Plugin) (%s)" % total_overwrites,
            overwrite_time,
        )

        performance_handler(
            unique_name, "Cache", "Generating and writing server/entry point", None
        )

        server_file_path = jp(replace_files, "server.java")

        if not os.path.exists(server_file_path):
            log(
                FATAL,
                f"{unique_name} Server file at {server_file_path} does not exist, {skip_message}",
            )

        server_import_file_path = jp(replace_files, "settings.json")
        if not os.path.exists(server_import_file_path):
            log(
                FATAL,
                f"{unique_name} Server config file at {server_import_file_path} does not exist, {skip_message}",
            )

        server_file = get_file_contents(server_file_path)
        server_import_file = json.loads(get_file_contents(server_import_file_path))
        # client_file = get_file_contents(client_file_path)
        pre_imports: list[str] = []
        pre_setups: list[str] = []
        # settings.json, you'll figure it out
        # Alright past me, I did because of your snazzy comment. Still hate you though
        for x in things_added:
            pre_imports.append(server_import_file[x]["import"])
            pre_setups.append(server_import_file[x]["setup"])

        imports = format_text("\n".join(pre_imports), self, mod_info, info_replace)
        setups = format_text("\n".join(pre_setups), self, mod_info, info_replace)

        server_file = format_text(
            server_file, self, mod_info, {"imports": imports, "setups": setups}
        )
        # client_file = format_text(client_file, self)

        write_to_file(jp(java_path, f"{self.id.title()}.java"), server_file)
        # write_to_file(jp(java_path, f"ClientEvents.java"), client_file)

        del server_file

        performance_add_end_marker(unique_name)


def import_mod(
    data: dict[str, Any] | str,
    mdk_folder: str,
    external_packs: Optional[list[str]] = None,
):
    """Creates a new instance of mod_class from exported data."""

    if isinstance(data, str):
        if os.path.exists(data):
            content = json.loads(get_file_contents(data))
        else:
            content = json.loads(data)
    else:
        content = data

    mod_data = content.get("mod", {})
    components_data = content.get("components", {})
    mod_class = Mod

    # Create mod instance
    mod_instance = mod_class(
        internal_id=mod_data["internal_id"],
        public_id=mod_data["public_id"],
        name=mod_data["name"],
        author=mod_data["author"],
        version=mod_data["version"],
        description=mod_data["description"],
        license=mod_data["license"],
        mdk_parent_folder=mdk_folder,
        external_packs=(
            (external_packs if external_packs else [])
            + get_surface_level_subdirectory(
                build_external_packs(content["external_packs"])
            )
            if content.get("external_packs")
            else []
        ),
    )

    # Import components
    for component_id, component_data in components_data.items():

        component_class = getattr(
            components,
            component_data["__export_class_identifier__"],
        )
        if component_class:
            mod_instance.components[component_id] = import_class(
                component_class, component_data
            )
        else:
            raise ValueError(f"Unknown component type for ID: {component_id}")

    return mod_instance


def export_mod(
    mod_class: "Mod", include_external_packs: bool
) -> dict[str, str | dict[str, Any]]:
    mod_things = {
        "internal_id": mod_class.internal_id,
        "public_id": mod_class.id,
        "name": mod_class.name,
        "author": mod_class.author,
        "version": mod_class.version,
        "description": mod_class.description,
        "license": mod_class.license,
    }
    components: dict[str, dict[str, Any]] = {}
    for component_id, component in mod_class.components.items():
        components[component_id] = export_class(component)

    final: dict[str, str | dict[str, Any]] = {
        "mod": mod_things,
        "components": components,
    }
    if include_external_packs:
        data = gather_external_packs(mod_class)
        final.update({"external_packs": data})
    return final


import shared


def gather_external_packs(mod_class: "Mod") -> dict[str, str]:
    files_to_check: list[str] = []
    for pack in mod_class.external_packs:
        for root, _, files in os.walk(pack):
            for file in files:
                files_to_check.append(os.path.normpath(os.path.join(root, file)))
    base = shared.base.Base440(None)
    return_files: dict[str, str] = {}

    for i in files_to_check:
        extension = i.split(".")[-1]
        if extension == "png":  # The specialized compression is like 40% better
            return_files.update({i: shared.image_compression.image_to_text(i)})
        else:
            return_files.update({i: base.encode(get_byte_contents(i))})
    return return_files


import tempfile


def build_external_packs(files: dict[str, str]):
    temp_dir = tempfile.mkdtemp()
    base = shared.base.Base440(None)

    for file_name, file_content in files.items():
        full_path = os.path.join(temp_dir, file_name)

        # Create any needed parent directories
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        extension = file_name.split(".")[-1]
        if extension == "png":
            content = shared.image_compression.text_to_image(file_content)
            content.save(full_path)
        else:
            content = base.decode(file_content)
            with open(full_path, "wb") as f:
                f.write(content)

    return temp_dir


def get_surface_level_subdirectory(path: str) -> list[str]:

    return [
        name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))
    ]
