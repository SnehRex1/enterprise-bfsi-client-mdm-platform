from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecordRef:
    """
    Identifies exactly one source-system record.

    Example:
        CORE + C00001234
    """

    source_system: str
    source_id: str


class UnionFind:
    """
    Union-Find / Disjoint Set data structure.

    It answers:

        "Which cluster does this record belong to?"

    Two important operations:

        find()
            Find the representative/root of a cluster.

        union()
            Merge two clusters together.
    """

    def __init__(self) -> None:
        # Every record initially points to itself.
        self.parent: dict[RecordRef, RecordRef] = {}

        # Rank helps keep the tree shallow.
        self.rank: dict[RecordRef, int] = {}

    def add(self, item: RecordRef) -> None:
        """
        Add a new record as its own cluster.
        """

        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item: RecordRef) -> RecordRef:
        """
        Find the root of the cluster containing item.

        Path compression:
        after finding the root, we connect the record directly
        to that root, making future lookups faster.
        """

        self.add(item)

        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])

        return self.parent[item]

    def union(self, left: RecordRef, right: RecordRef) -> None:
        """
        Merge the clusters containing left and right.
        """

        self.add(left)
        self.add(right)

        left_root = self.find(left)
        right_root = self.find(right)

        # Already in the same cluster.
        if left_root == right_root:
            return

        # Union by rank:
        # attach the smaller tree to the larger tree.
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root

        self.parent[right_root] = left_root

        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1

    def groups(self) -> dict[RecordRef, list[RecordRef]]:
        """
        Convert the internal Union-Find structure into:

            cluster_root -> members
        """

        grouped: dict[RecordRef, list[RecordRef]] = {}

        for item in self.parent:
            root = self.find(item)
            grouped.setdefault(root, []).append(item)

        return grouped