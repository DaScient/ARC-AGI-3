"""
ARC-AGI-3 Solver — The Pentarchy of Reason
===========================================

A neuro-symbolic solver for ARC-AGI 3 competition tasks.
"""

from .perception import GridPerception
from .dsl import DSLRegistry
from .synthesizer import ProgramSynthesizer
from .verifier import SymbolicVerifier
from .controller import ActiveInferenceController
from .solver import ARCSolver

__all__ = [
    "GridPerception",
    "DSLRegistry",
    "ProgramSynthesizer",
    "SymbolicVerifier",
    "ActiveInferenceController",
    "ARCSolver",
]
