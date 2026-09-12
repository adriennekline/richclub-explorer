"""RichClub Explorer: reproducible rich-club analysis for scientific networks."""

from .analysis import RichClubResult, analyze, rich_club_curve
from .io import load_adjacency_matrix, load_edge_list
from .membership import classify_edges, rich_nodes
from .validation import NetworkValidationError, ValidationReport, validate_network

__all__ = [
    "NetworkValidationError",
    "RichClubResult",
    "ValidationReport",
    "analyze",
    "classify_edges",
    "load_adjacency_matrix",
    "load_edge_list",
    "rich_club_curve",
    "rich_nodes",
    "validate_network",
]

__version__ = "0.1.0"
