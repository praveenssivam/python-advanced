"""
07_factory_pattern.py
=======================
Factory Pattern — centralise object creation behind a registration
mechanism so callers create objects by name, not by constructor.

Problem:  Object creation scattered across the codebase with if/elif.
Solution: A registry-based factory; registering a new type is the only
          change needed when a new connector/format/source is added.

Run:
    python demo/module-03/07_factory_pattern.py
"""

from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT: data source connectors
#
# Without a factory, every caller does:
#     if config["type"] == "csv":  conn = CSVConnector(...)
#     elif config["type"] == "json": conn = JSONConnector(...)
#     ...
#
# That same if/elif block is duplicated across the codebase.
# Adding ParquetConnector means finding and updating every copy.
#
# With a factory and registry:
#     conn = ConnectorFactory.create(config)
#
# Flow for ConnectorFactory.create(config):
#   1. Look up config["type"] in the registry dict
#   2. If found → call connector_class(**config)
#   3. If not found → raise ValueError listing known types
#
# To add a new connector: call ConnectorFactory.register("parquet", ParquetConnector)
# before the first .create() call. No other code changes.
# ══════════════════════════════════════════════════════════════════════════════

class DataConnector(ABC):
    """Abstract connector: knows how to open a connection and read rows."""

    def __init__(self, path: str, **kwargs):
        self.path = path
        self._options = kwargs

    @abstractmethod
    def read(self) -> list[dict]:
        """Return rows from the source."""
        ...

    @property
    @abstractmethod
    def format_name(self) -> str: ...

    def __repr__(self) -> str:
        return f"{type(self).__name__}(path={self.path!r})"


# ── Concrete connector implementations ──────────────────────────────────────

class CSVConnector(DataConnector):
    format_name = "csv"

    def read(self) -> list[dict]:
        print(f"  [CSVConnector] reading {self.path}")
        # Simulated read
        return [{"id": 1, "value": "csv_row_a"}, {"id": 2, "value": "csv_row_b"}]


class JSONConnector(DataConnector):
    format_name = "json"

    def read(self) -> list[dict]:
        print(f"  [JSONConnector] reading {self.path}")
        return [{"id": 1, "value": "json_row_a"}]


class ParquetConnector(DataConnector):
    """NEW connector — registered with the factory, no other code changes."""

    format_name = "parquet"

    def __init__(self, path: str, compression: str = "snappy", **kwargs):
        super().__init__(path, **kwargs)
        self._compression = compression

    def read(self) -> list[dict]:
        print(f"  [ParquetConnector] reading {self.path} (compression={self._compression})")
        return [{"id": 1, "value": "parquet_row_a"}, {"id": 2, "value": "parquet_row_b"}]


# ── Factory ──────────────────────────────────────────────────────────────────

class ConnectorFactory:
    """Registry-based factory for DataConnector instances.

    Class-level registry maps type strings to connector classes.
    Connectors register themselves (or are registered at module load time).
    The caller only needs to know the type string and config dict.
    """

    _registry: dict[str, type[DataConnector]] = {}

    @classmethod
    def register(cls, type_name: str, connector_class: type[DataConnector]) -> None:
        """Register a connector class under a type string key."""
        cls._registry[type_name] = connector_class

    @classmethod
    def create(cls, config: dict) -> DataConnector:
        """Create a connector from a config dict.

        config must contain a "type" key. All other keys are forwarded
        as keyword arguments to the connector's constructor.

        Flow:
          1. Extract type_name from config["type"]
          2. Look up type_name in _registry
          3. Call connector_class(**remaining_config) → return instance
        """
        config = dict(config)           # don't modify the caller's dict
        type_name = config.pop("type")  # extract type key
        if type_name not in cls._registry:
            known = sorted(cls._registry.keys())
            raise ValueError(f"Unknown connector type {type_name!r}. Known: {known}")
        connector_class = cls._registry[type_name]
        return connector_class(**config)

    @classmethod
    def known_types(cls) -> list[str]:
        return sorted(cls._registry.keys())


# ── Register built-in connectors at module load time ────────────────────────
ConnectorFactory.register("csv",     CSVConnector)
ConnectorFactory.register("json",    JSONConnector)
ConnectorFactory.register("parquet", ParquetConnector)


# ── Scattered-creation anti-pattern (for comparison) ────────────────────────

def create_connector_bad(config: dict) -> DataConnector:
    """BAD: if/elif scattered creation. Each new type requires editing here."""
    t = config["type"]
    if t == "csv":
        return CSVConnector(config["path"])
    elif t == "json":
        return JSONConnector(config["path"])
    # ← Adding parquet means another elif here, and in every other copy of this block
    raise ValueError(f"Unknown type: {t}")


def demo_factory():
    print("=" * 60)
    print("Factory Pattern — create connectors from config dicts")
    print("=" * 60)

    print()
    print("Known connector types:", ConnectorFactory.known_types())
    print()

    # Config-driven creation — the caller doesn't name constructor arguments
    configs = [
        {"type": "csv",     "path": "data/sales.csv"},
        {"type": "json",    "path": "data/events.json"},
        {"type": "parquet", "path": "data/trips.parquet", "compression": "gzip"},
    ]

    print("Creating and reading via factory:")
    for cfg in configs:
        # Flow: ConnectorFactory.create(cfg)
        #   → pop "type" = "csv" / "json" / "parquet"
        #   → look up in _registry → find class
        #   → CSVConnector(path="data/sales.csv") etc.
        conn = ConnectorFactory.create(cfg)
        rows = conn.read()
        print(f"    {conn!r} → {len(rows)} row(s)")

    print()
    print("Unknown type raises a helpful error:")
    try:
        ConnectorFactory.create({"type": "excel", "path": "data/report.xlsx"})
    except ValueError as e:
        print(f"  ValueError: {e}")


def demo_new_connector():
    print("\n" + "=" * 60)
    print("Adding a new connector type — only one change needed")
    print("=" * 60)
    print()

    class XMLConnector(DataConnector):
        """Third-party or late-registered connector."""
        format_name = "xml"

        def read(self) -> list[dict]:
            print(f"  [XMLConnector] parsing {self.path}")
            return [{"element": "row1"}, {"element": "row2"}]

    # One registration call — factory onwards discovers it
    ConnectorFactory.register("xml", XMLConnector)

    print("Registered XMLConnector. Known types:", ConnectorFactory.known_types())
    conn = ConnectorFactory.create({"type": "xml", "path": "data/feed.xml"})
    rows = conn.read()
    print(f"  {conn!r} → {len(rows)} row(s)")

    print()
    print("No existing code was modified. Only XMLConnector was written,")
    print("and ConnectorFactory.register('xml', XMLConnector) was called once.")


def main():
    demo_factory()
    demo_new_connector()


if __name__ == "__main__":
    main()
