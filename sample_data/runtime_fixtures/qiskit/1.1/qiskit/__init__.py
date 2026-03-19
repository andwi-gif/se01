"""Offline Qiskit runtime fixture for version 1.1."""

__version__ = "1.1"


class QuantumCircuit:
    """Tiny stub used by offline execution tests."""

    def __init__(self, qubits: int = 0) -> None:
        self.qubits = qubits
