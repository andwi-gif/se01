"""Offline Qiskit runtime fixture for version 0.45."""

__version__ = "0.45"


class QuantumCircuit:
    """Tiny stub used by offline execution tests."""

    def __init__(self, qubits: int = 0) -> None:
        self.qubits = qubits
