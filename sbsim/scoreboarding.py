import os
from dataclasses import dataclass


@dataclass
class InstructionType:
    LOAD = 0
    STORE = 1
    ADD_SUB = 2
    MULT = 3
    DIVD = 4


class ScoreboardingSIM:

    OPCODE_MAP = {
        "LW": (int, InstructionType.LOAD),
        "LD": (float, InstructionType.LOAD),
        "SW": (int, InstructionType.STORE),
        "SD": (float, InstructionType.STORE),
        "SUB": (int, InstructionType.ADD_SUB),
        "SUBD": (float, InstructionType.ADD_SUB),
        "ADD": (int, InstructionType.ADD_SUB),
        "ADDD": (float, InstructionType.ADD_SUB),
        "MULTD": (float, InstructionType.MULT),
        "DIVD": (float, InstructionType.DIVD),
    }

    REG_PREFIXES = {"int": "r", "float": "f"}

    def __init__(self, file_path: os.path) -> None:
        self.parse_file(file_path)

    def parse_file(self, file_path: os.path) -> None:
        """Parse inputed file and build attributes"""
        with open(file_path, "r") as f:
            for line in f:
                fields = line.strip().replace(",", " ").split()
                print(fields)

    def build_instruction_status(self) -> None:
        """Build instruction table based in the inputed instructions"""
        pass

    def build_functional_unit_status(self) -> None:
        """Build functional unit table based in the inputed Functional Units"""
        self.functional_unit_table = {}
        functional_unit_elements = {
            "busy": None,
            "op": None,
            "fi": None,
            "fj": None,
            "fk": None,
            "qj": None,
            "qk": None,
            "rj": None,
            "rk": None,
        }
        for fu in self.functional_units.keys():
            self.functional_unit_table[fu] = functional_unit_elements
            self.functional_unit_table[fu]["n_cycles"] = self.functional_units[
                "n_cycles"
            ]

    def build_register_status(self, regr: int = 32, regf: int = 32) -> None:
        """Build register table based in the inputed Functional Units"""
        self.register_table = {}
        for i in range(regr):
            reg_idx = i + 1
            self.register_table[
                self.REG_PREFIXES["int"] + str(reg_idx)
            ] = 0  # Start all registers with 0
        for i in range(regf):
            reg_idx = i + 1
            self.register_table[
                self.REG_PREFIXES["float"] + str(reg_idx)
            ] = 0  # Start all registers with 0
