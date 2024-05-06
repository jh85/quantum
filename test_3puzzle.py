from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

def toNum(q):
    if q == "00": return "1"
    if q == "01": return "2"
    if q == "10": return "3"
    if q == "11": return "X"

def print_qbits(q):
    print(toNum(q[0:2]), toNum(q[2:4]))
    print(toNum(q[4:6]), toNum(q[6:8]))

def move(qc, pathbit, tracebits):
    # if both bit-0 and bit-1 are 1, X is in the cell.
    # Set tracebits[0] to 1
    qc.ccx(0,1,tracebits[0])
    qc.ccx(2,3,tracebits[1])
    qc.ccx(4,5,tracebits[2])
    qc.ccx(6,7,tracebits[3])
    qc.barrier()

    # if pathbit is 1, move [X] counter-clock wise
    qc.ccx(tracebits[0],pathbit,8)
    qc.cswap(8, 0, 4)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 1, 5)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[0],pathbit,8)

    # if pathbit is 0, move [X] clock wise
    qc.x(pathbit)
    qc.ccx(tracebits[0],pathbit,8)
    qc.cswap(8, 0, 2)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 1, 3)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[0],pathbit,8)
    qc.x(pathbit)
    qc.barrier()

    qc.ccx(tracebits[1],pathbit,8)
    qc.cswap(8, 2, 0)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 3, 1)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[1],pathbit,8)
    qc.x(pathbit)
    qc.ccx(tracebits[1],pathbit,8)
    qc.cswap(8, 2, 6)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 3, 7)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[1],pathbit,8)
    qc.x(pathbit)
    qc.barrier()

    qc.ccx(tracebits[2],pathbit,8)
    qc.cswap(8, 4, 6)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 5, 7)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[2],pathbit,8)
    qc.x(pathbit)
    qc.ccx(tracebits[2],pathbit,8)
    qc.cswap(8, 4, 0)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 5, 1)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[2],pathbit,8)
    qc.x(pathbit)
    qc.barrier()

    qc.ccx(tracebits[3],pathbit,8)
    qc.cswap(8, 6, 2)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 7, 3)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[3],pathbit,8)
    qc.x(pathbit)
    qc.ccx(tracebits[3],pathbit,8)
    qc.cswap(8, 6, 4)  # If qubit 13 is |1⟩, swap qubits 11 and 8
    qc.cswap(8, 7, 5)  # If qubit 13 is |1⟩, swap qubits 12 and 8
    qc.ccx(tracebits[3],pathbit,8)
    qc.x(pathbit)
    qc.barrier()

    return qc

def main():
    qc = QuantumCircuit(30,8)

    # Initial position
    # +-----------+
    # | [3] | [X] |
    # | 7 6 | 5 4 |
    # +-----------+
    # | [1] | [2] |
    # | 3 2 | 1 0 |
    # +-----------+

    # num |First bit, Second bit>
    # 1   |00>
    # 2   |10>
    # 3   |01>
    # X   |11>

    # set position bits
    qc.x(0)
    qc.x(4)
    qc.x(5)
    qc.x(7)

    # superposition path bits
    qc.h(13)
    qc.h(18)
    qc.h(23)
    qc.h(28)
    qc.barrier()

    # Move the [X] tile to counterclock / clock wise for four times
    for i in range(4):
        qc = move(qc, 13+i*5, list(range(9+i*5,13+i*5)))

    qc.measure(list(range(0,8)),
               list(range(0,8)))

    backend = AerSimulator(device="CPU")
    compiled_circuit = transpile(qc, backend)
    job = backend.run(compiled_circuit, shots=1024)
    result = job.result()
    counts = result.get_counts()
    for qbit,cnt in counts.items():
        print(f"Qbit: {qbit} count: {cnt}")
        print_qbits(qbit)
    
main()
