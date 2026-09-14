"""Four ownership modules composed into one immutable action registry.

Module ownership is separate from capability packs: a module never grants an
agent permission to use its actions. Rules and baseline policy still decide.
"""
from types import MappingProxyType
from . import common, memory, coach, task_specific

MODULE_SPECS = MappingProxyType({
    "common": common.SPECS,
    "memory": memory.SPECS,
    "coach": coach.SPECS,
    "task_specific": task_specific.SPECS,
})
ALL_SPECS = tuple(spec for specs in MODULE_SPECS.values() for spec in specs)
if len({spec.name for spec in ALL_SPECS}) != len(ALL_SPECS):
    raise ValueError("An action must be defined in exactly one module")
if any(spec.module != owner for owner, specs in MODULE_SPECS.items() for spec in specs):
    raise ValueError("Action module ownership does not match its definition")
ACTION_REGISTRY = MappingProxyType({spec.name: spec for spec in ALL_SPECS})
MODULE_ACTION_NAMES = MappingProxyType({
    name: frozenset(spec.name for spec in specs) for name, specs in MODULE_SPECS.items()
})
TOOL_ACTION_NAMES = frozenset(spec.name for spec in ALL_SPECS if spec.is_tool)
