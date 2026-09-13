import importlib.util
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "deploy/surreal-backup/order_restore.py"
SPEC = importlib.util.spec_from_file_location("restore_order", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_dependency_order_preserves_opaque_multiline_data_and_schema():
    raw = b"""-- OPTION
OPTION IMPORT;
DEFINE USER fixture ON DATABASE PASSHASH 'opaque-test-only';
-- TABLE: confirms
DEFINE TABLE confirms TYPE RELATION IN node OUT edge ENFORCED SCHEMAFULL;
-- TABLE DATA: confirms
INSERT RELATION [{ id: confirms:a, in: node:a, out: edge:a }];
-- TABLE: edge
DEFINE TABLE edge TYPE RELATION IN node OUT node ENFORCED SCHEMAFULL;
-- TABLE DATA: edge
INSERT RELATION [{ id: edge:a, in: node:a, out: node:b }];
-- TABLE: node
DEFINE TABLE node TYPE NORMAL SCHEMAFULL;
-- TABLE DATA: node
INSERT [{ id: node:a, text: 'opaque; -- TABLE DATA: confirms
fake multiline payload; \\\'quoted\\\' [ ]' }, {id:node:b}];
"""
    ordered, receipt = MODULE.reorder(raw)
    assert receipt["data_order"] == ["node", "edge", "confirms"]
    assert ordered.index(b"INSERT [{") < ordered.index(b"INSERT RELATION [{ id: edge")
    assert ordered.index(b"id: edge:a, in:") < ordered.index(b"id: confirms:a, in:")
    assert ordered.count(b"ENFORCED") == 2
    original_statements, _ = MODULE.statements(raw.decode())
    output_statements, _ = MODULE.statements(ordered.decode())
    assert sorted(original_statements) == sorted(output_statements)


@pytest.mark.parametrize("tail", ["DELETE node;", "INSERT [{id:node:a}];", "INSERT ['unclosed;"])
def test_rejects_unknown_or_ambiguous_data(tail):
    raw = f"OPTION IMPORT; DEFINE TABLE node TYPE NORMAL SCHEMAFULL; {tail}".encode()
    with pytest.raises(ValueError):
        MODULE.reorder(raw)


def test_rejects_cross_table_dependency_cycles():
    raw = b"""OPTION IMPORT;
DEFINE TABLE a TYPE RELATION IN b OUT b ENFORCED SCHEMAFULL;
DEFINE TABLE b TYPE RELATION IN a OUT a ENFORCED SCHEMAFULL;
"""
    with pytest.raises(ValueError, match="Cyclic"):
        MODULE.reorder(raw)
