from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum


class PatternType(Enum):
    """Enumeration of built-in pattern types."""

    SUPERVISOR = "supervisor"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    CONSENSUS = "consensus"
    COMPETITIVE = "competitive"
    CUSTOM = "custom"


@dataclass
class PatternMetadata:
    """Metadata for collaboration patterns."""

    name: str
    description: str
    pattern_type: PatternType
    min_agents: int = 1
    max_agents: Optional[int] = None
    requires_supervisor: bool = False
    requires_judge: bool = False
    composable: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class GraphTopology:
    """Represents a graph topology for a pattern."""

    nodes: List[str]
    edges: List[tuple]  # List of (source, target) tuples
    entry_point: str = "start"
    exit_point: str = "end"
    special_nodes: Dict[str, str] = field(
        default_factory=dict
    )  # e.g., {"supervisor": "coordinator"}

    def validate(self) -> bool:
        """Validate the graph topology."""
        # Check all nodes in edges exist in nodes list
        edge_nodes = set()
        for source, target in self.edges:
            edge_nodes.add(source)
            edge_nodes.add(target)
        return edge_nodes.issubset(set(self.nodes))


class CollaborationPattern(ABC):
    """
    Base class for all collaboration patterns.
    Each pattern must implement methods to generate graph topology and routing logic.
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name or self.__class__.__name__
        self._metadata = self._create_metadata()
        self._subpatterns: List["CollaborationPattern"] = []

    @abstractmethod
    def _create_metadata(self) -> PatternMetadata:
        """Create metadata for this pattern."""
        pass

    @abstractmethod
    def build_topology(self, agents: List[str], **kwargs) -> GraphTopology:
        """
        Build the graph topology for the pattern.
        Args:
            agents: List of agent names/IDs involved in the pattern.
            **kwargs: Additional pattern-specific parameters.
        Returns:
            GraphTopology object representing the pattern structure.
        """
        pass

    @abstractmethod
    def create_router(self, **kwargs) -> Callable[[Dict[str, Any]], str]:
        """
        Create a router function for this pattern.
        Args:
            **kwargs: Pattern-specific routing configuration.
        Returns:
            A callable that takes state and returns next node name.
        """
        pass

    def compose(self, other: "CollaborationPattern", **kwargs) -> "CompositePattern":
        """
        Compose this pattern with another pattern.
        Args:
            other: Another collaboration pattern to compose with.
            **kwargs: Composition configuration.
        Returns:
            A new CompositePattern combining both patterns.
        """
        from .composite import CompositePattern

        return CompositePattern(patterns=[self, other], **kwargs)

    @property
    def metadata(self) -> PatternMetadata:
        """Get pattern metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get pattern name."""
        return self._name

    def validate_agents(self, agents: List[str]) -> bool:
        """
        Validate that the agent list meets pattern requirements.
        Args:
            agents: List of agent names.
        Returns:
            True if valid, raises ValueError otherwise.
        """
        if len(agents) < self._metadata.min_agents:
            raise ValueError(
                f"Pattern {self.name} requires at least {self._metadata.min_agents} agents, "
                f"got {len(agents)}"
            )
        if self._metadata.max_agents and len(agents) > self._metadata.max_agents:
            raise ValueError(
                f"Pattern {self.name} supports at most {self._metadata.max_agents} agents, "
                f"got {len(agents)}"
            )
        return True


class PatternRegistry:
    """
    Registry for collaboration patterns.
    Allows registration, lookup, and detection of patterns.
    """

    _instance = None
    _patterns: Dict[str, Type[CollaborationPattern]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, pattern_type: str, pattern_class: Type[CollaborationPattern]):
        """Register a pattern type."""
        cls._patterns[pattern_type] = pattern_class

    @classmethod
    def get(cls, pattern_type: str) -> Optional[Type[CollaborationPattern]]:
        """Get a pattern class by type."""
        return cls._patterns.get(pattern_type)

    @classmethod
    def list_patterns(cls) -> List[str]:
        """List all registered pattern types."""
        return list(cls._patterns.keys())

    @classmethod
    def create(cls, pattern_type: str, **kwargs) -> CollaborationPattern:
        """Create a pattern instance."""
        pattern_class = cls.get(pattern_type)
        if not pattern_class:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
        return pattern_class(**kwargs)

    @classmethod
    def detect_pattern(cls, topology: GraphTopology) -> Optional[PatternType]:
        """
        Detect pattern type from graph topology.
        Args:
            topology: Graph topology to analyze.
        Returns:
            Detected PatternType or None.
        """
        nodes = set(topology.nodes)
        edges = topology.edges

        # Build adjacency lists
        outgoing = {node: [] for node in nodes}
        incoming = {node: [] for node in nodes}
        for source, target in edges:
            outgoing[source].append(target)
            incoming[target].append(source)

        # Detection heuristics

        # Sequential: Linear chain
        if cls._is_sequential(nodes, outgoing, incoming):
            return PatternType.SEQUENTIAL

        # Parallel: All agents start from same node, end at same node
        if cls._is_parallel(nodes, outgoing, incoming, topology):
            return PatternType.PARALLEL

        # Supervisor: One node connects to all others bidirectionally
        if cls._is_supervisor(nodes, outgoing, incoming):
            return PatternType.SUPERVISOR

        # Consensus: All agents converge to one decision node
        if cls._is_consensus(nodes, outgoing, incoming):
            return PatternType.CONSENSUS

        # Competitive: Similar to consensus but with judge semantics
        if cls._is_competitive(nodes, outgoing, incoming, topology):
            return PatternType.COMPETITIVE

        return None

    @staticmethod
    def _is_sequential(nodes, outgoing, incoming):
        """Check if topology is sequential."""
        # Each node (except start/end) has exactly one incoming and one outgoing
        for node in nodes:
            if node in ["start", "end"]:
                continue
            if len(incoming[node]) != 1 or len(outgoing[node]) != 1:
                return False
        return True

    @staticmethod
    def _is_parallel(nodes, outgoing, incoming, topology):
        """Check if topology is parallel."""
        start = topology.entry_point
        end = topology.exit_point

        # Check if there's a join node
        has_join = "join" in topology.special_nodes

        if has_join:
            join_node = topology.special_nodes["join"]
            agent_nodes = nodes - {start, end, join_node}
            # All agents connect from start to join
            return all(
                start in incoming[agent] and join_node in outgoing[agent]
                for agent in agent_nodes
            )
        else:
            # All non-start/end nodes connected from start and to end directly
            agent_nodes = nodes - {start, end}
            # Must have start edges to all agents
            if not all(start in incoming[agent] for agent in agent_nodes):
                return False
            # Must have end edges from all agents
            if not all(end in outgoing[agent] for agent in agent_nodes):
                return False
            # And no other intermediate nodes
            return len(agent_nodes) >= 2

    @staticmethod
    def _is_supervisor(nodes, outgoing, incoming):
        """Check if topology is supervisor."""
        # Find candidate supervisor: node with many outgoing and incoming edges
        for node in nodes:
            if node in ["start", "end"]:
                continue
            if len(outgoing[node]) >= 2 and len(incoming[node]) >= 2:
                # Check if it connects to most other nodes
                connected = set(outgoing[node]) | set(incoming[node])
                if len(connected) >= len(nodes) - 2:  # Excluding start/end
                    return True
        return False

    @staticmethod
    def _is_consensus(nodes, outgoing, incoming):
        """Check if topology is consensus."""
        # Find node with many incoming edges (consensus node)
        for node in nodes:
            if node in ["start", "end"]:
                continue
            if len(incoming[node]) >= 2:
                # Other nodes should have fewer incoming edges
                return True
        return False

    @staticmethod
    def _is_competitive(nodes, outgoing, incoming, topology):
        """Check if topology is competitive."""
        # Similar to consensus but look for 'judge' in special nodes
        if "judge" in topology.special_nodes:
            return True
        # Otherwise use same heuristic as consensus
        return PatternRegistry._is_consensus(nodes, outgoing, incoming)
