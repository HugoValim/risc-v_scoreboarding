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
        "ild": (int, InstructionType.LOAD),
        "fld": (float, InstructionType.LOAD),
        "isw": (int, InstructionType.STORE),
        "fsd": (float, InstructionType.STORE),
        "isub": (int, InstructionType.ADD_SUB),
        "fsub": (float, InstructionType.ADD_SUB),
        "iadd": (int, InstructionType.ADD_SUB),
        "fadd": (float, InstructionType.ADD_SUB),
        "fmul": (float, InstructionType.MULT),
        "fdiv": (float, InstructionType.DIVD),
    }

    REG_PREFIXES = {"int": "r", "float": "f"}

    FUNCTIONAL_UNITS = ["int", "mult", "add", "div"]

    def __init__(self, file_path: os.path) -> None:
        self.file = file_path

    def execute(self):
        """Method to execute the simultor"""
        self.functional_units_config = self.parse_file()

    def parse_file(self) -> tuple[dict, dict]:
        """Parse inputed file and build attributes"""
        functional_units_config = {}
        instructions_to_execute = {}
        with open(self.file, "r") as f:
            for line in f:
                fields = line.strip().replace(",", " ").split()
                if not fields:  # Skip blank lines
                    continue
                elif fields[0].lower() in self.FUNCTIONAL_UNITS:
                    functional_units_config[fields[0]] = {}
                    functional_units_config[fields[0]]["n_units"] = fields[1]
                    functional_units_config[fields[0]]["n_cycle"] = fields[2]
                    continue
                elif fields[0].lower() in self.OPCODE_MAP:
                    instructions_to_execute[fields[0]] = fields[1:]

            return functional_units_config, instructions_to_execute

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
