strip_wood_procedure = '[{"action":"if","condition":{"action":"is_itemstack_tagged_with","itemstack":{"action":"get_main_hand","entity":{"action":"get_event_entity"}},"tag":"axe"},"code":[{"action":"replace_block_and_keep_blockstate_and_nbt","block":{"action":"get_block_by_id","id":"minecraft:stripped_oak_log"},"pos":{"action":"get_event_pos"}}]}]'
import json
from ender_py.procedures import ProcedureInternal


procedure = json.loads(strip_wood_procedure)

procedure_blocks_path = "ender_py/procedures"

requested_version = "forge-1.20.1"

new = ProcedureInternal()
new.load_blocks(procedure_blocks_path)
new.handle_event(procedure, requested_version, "none")


# print("FINAL")
# print(code)
# print("END")
# print(required_imports)
# print(current_required_contexts)
# print(current_contexts)
# print(custom_contexts)
