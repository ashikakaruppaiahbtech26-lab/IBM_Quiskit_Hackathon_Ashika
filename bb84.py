"""  BB84 quantum key distribution -- a small Qiskit simulation.

Everything here runs on the Qiskit Aer SIMULATOR (no real quantum hardware).

Conventions
-----------
bit   : 0 or 1 (the secret value Alice wants to send)
basis : 0 = Z / "rectilinear" basis  (states |0>, |1>)
        1 = X / "diagonal"    basis  (states |+>, |->)

The four BB84 states are made with two gates:
    X gate  -> flips |0> to |1>           (encodes bit = 1)
    H gate  -> Hadamard, moves Z basis <-> X basis  (encodes basis = 1)
Measuring in the X basis = apply H, then measure normally. """

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError


def random_bits(n, rng):
    """n random 0/1 values as a numpy array."""
    return rng.integers(0, 2, size=n)


def build_circuit(bits, prep_bases, meas_bases):
    """prep_bases : basis used to prepare each qubit
    meas_bases : basis used to measure each qubit"""
    n = len(bits)
    qc = QuantumCircuit(n, n)
    for i in range(n):
        if bits[i] == 1:
            qc.x(i)                 # encodes the bit value
        if prep_bases[i] == 1:
            qc.h(i)                 # encodes the basis choice
    qc.barrier()                    # "the qubits travel here"
    for i in range(n):
        if meas_bases[i] == 1:
            qc.h(i)                 # measures in the X basis = H then Z-measure
    qc.measure(range(n), range(n))
    return qc


def make_backend(noise=0.0):
    if noise > 0:
        nm = NoiseModel()
        nm.add_all_qubit_readout_error(
            ReadoutError([[1 - noise, noise], [noise, 1 - noise]])
        )
        return AerSimulator(method="stabilizer", noise_model=nm)
    return AerSimulator(method="stabilizer")


def prepare_and_measure(bits, prep_bases, meas_bases, backend, seed):
    """Running the circuit once (1 shot) and returning the measured bits."""
    qc = build_circuit(bits, prep_bases, meas_bases)
    counts = backend.run(qc, shots=1, seed_simulator=int(seed)).result().get_counts()
    bitstring = next(iter(counts))                 
    # Qiskit prints qubit 0 on the RIGHT, so reverse to get qubit order.
    return np.array([int(b) for b in reversed(bitstring)])


def run_bb84(n=256, eve=False, eve_fraction=1.0, noise=0.0, seed=42):
    rng = np.random.default_rng(seed)
    backend = make_backend(noise)

    # Alice: random bits and random bases
    alice_bits = random_bits(n, rng)
    alice_bases = random_bits(n, rng)
    # Bob: random measurement bases
    bob_bases = random_bits(n, rng)

    if not eve:
        # Alice's qubits go straight to Bob.
        bob_bits = prepare_and_measure(alice_bits, alice_bases, bob_bases,
                                       backend, seed + 1)
        intercepted = np.zeros(n, dtype=bool)
    else:
        intercepted = rng.random(n) < eve_fraction
        eve_bases = random_bits(n, rng)

        eve_meas_bases = np.where(intercepted, eve_bases, alice_bases)
        eve_bits = prepare_and_measure(alice_bits, alice_bases, eve_meas_bases,
                                       backend if noise == 0 else make_backend(0),
                                       seed + 2)
        eve_prep_bases = eve_meas_bases
        bob_bits = prepare_and_measure(eve_bits, eve_prep_bases, bob_bases,
                                       backend, seed + 1)

    # Sifting: Alice and Bob publicly compare bases (never bits) and keep only the positions where they happened to choose the same basis.
    keep = alice_bases == bob_bases
    alice_key = alice_bits[keep]
    bob_key = bob_bits[keep]

    return {
        "n": n, "eve": eve, "noise": noise, "seed": seed,
        "alice_bits": alice_bits, "alice_bases": alice_bases,
        "bob_bases": bob_bases, "bob_bits": bob_bits,
        "intercepted": intercepted, "keep": keep,
        "alice_key": alice_key, "bob_key": bob_key,
        "error_rate": error_rate(alice_key, bob_key),
    }


def error_rate(key_a, key_b):
    if len(key_a) == 0:
        return float("nan")
    return float(np.mean(key_a != key_b))



def detection_probability(alice_key, bob_key, k, trials=2000, seed=0):
 
    rng = np.random.default_rng(seed)
    k = min(k, len(alice_key))
    caught = 0
    for _ in range(trials):
        idx = rng.choice(len(alice_key), size=k, replace=False)
        if np.any(alice_key[idx] != bob_key[idx]):
            caught += 1
    return caught / trials


def theory_detection(k, p_error=0.25):
    #With per-bit error 25%, P(catch) = 1 - (3/4)^k.
    return 1 - (1 - p_error) ** k
