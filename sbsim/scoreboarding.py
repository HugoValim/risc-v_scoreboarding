import os
from dataclasses import dataclass

import pandas as pd


class ScoreboardingSIM:

    FUNCTIONAL_UNITS = ["int", "mult", "add", "div"]

    OPCODE_MAP = {
        "ild": "int",
        "fld": "add",
        "isw": "int",
        "fsd": "add",
        "isub": "int",
        "fsub": "add",
        "iadd": "int",
        "fadd": "add",
        "fmul": "mult",
        "fdiv": "div",
    }

    REG_PREFIXES = {"int": "x", "float": "f"}

    def __init__(self, file_path: os.path) -> None:
        self.file = file_path

    def execute(self):
        """Method to execute the simultor"""
        self.instruction_table = {}
        self.functional_units_config, self.instructions_to_execute = self.parse_file()
        self.build_status()
        self.loop()

    @staticmethod
    def add_prefix_to_instructions(
        instruction_now: str, current_instructions: dict
    ) -> str:
        """Add a prefix to every instruction to indentify different ones in the execution"""
        idx = 0
        prefix = "_"
        for instruction in current_instructions.keys():
            if instruction_now == instruction.split("_")[0]:
                idx += 1
        instruction_idx = instruction_now + prefix + str(idx)
        return instruction_idx

    @staticmethod
    def remove_instruction_idx(instruction: str):
        """Get only the raw name of the instruction without its index"""
        return instruction.split("_")[0]

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
                    functional_units_config[fields[0]]["n_units"] = int(fields[1])
                    functional_units_config[fields[0]]["n_cycles"] = int(fields[2])
                    continue
                elif fields[0].lower() in self.OPCODE_MAP:
                    parsed_regs = []
                    for reg in fields[1:]:
                        if "(" in reg:
                            reg = reg.split("(")[1].split(")")[
                                0
                            ]  # Get only the reg and dont care for the displacement
                        parsed_regs.append(reg)
                    instruction_with_index = self.add_prefix_to_instructions(
                        fields[0], instructions_to_execute
                    )
                    instructions_to_execute[instruction_with_index] = parsed_regs
                    if len(instructions_to_execute[instruction_with_index]) == 2:
                        instructions_to_execute[instruction_with_index].append(None)

            return functional_units_config, instructions_to_execute

    def build_table_from_array(self) -> pd.DataFrame:
        """Build a pandas DtaFrame form an array"""
        stages = ["issue", "read", "ex", "write"]
        instructions = [i for i in self.instructions_to_execute.keys()]
        initialize_w_none = [None for i in range(len(instructions))]
        table = {"instruction": instructions}
        table_stages = {stage: initialize_w_none for stage in stages}
        table.update(table_stages)
        return pd.DataFrame(table)

    def build_instruction_status(self, lap: int) -> None:
        """Build instruction table based in the inputed instructions"""
        stages = ["issue", "read", "ex", "write"]
        instructions = [i for i in self.instructions_to_execute.keys()]
        self.instruction_table[instructions[lap]] = {}
        for i in stages:
            self.instruction_table[instructions[lap]][i] = None

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
        for fu in self.functional_units_config.keys():
            self.functional_unit_table[fu] = []
            for i in range(self.functional_units_config[fu]["n_units"]):
                dict_now = functional_unit_elements.copy()
                dict_now["n_cycles"] = self.functional_units_config[fu]["n_cycles"]
                self.functional_unit_table[fu].append(dict_now)

    def build_register_status(self, regr: int = 32, regf: int = 32) -> None:
        """Build register table based in the inputed Functional Units"""
        self.register_table = {}
        for i in range(regr):
            reg_idx = i + 1
            self.register_table[
                self.REG_PREFIXES["int"] + str(reg_idx)
            ] = None  # Start all registers with 0
        for i in range(regf):
            reg_idx = i + 1
            self.register_table[
                self.REG_PREFIXES["float"] + str(reg_idx)
            ] = None  # Start all registers with 0

    def build_status(self):
        """Build all needed status table"""
        self.build_functional_unit_status()
        self.build_register_status()

    def issue_stage(self, lap: int):
        """Process the issue stage, making the needed check, basically the required F.U. mustn't busy and the dest register must no be free (avoiding WAW hazard)"""
        self.build_instruction_status(lap)
        for instruction in self.instruction_table:
            if self.instruction_table[instruction]["issue"] is not None:
                #  Issue already occured, skip this one
                continue
            for fu in self.functional_unit_table[
                self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
            ]:
                if (
                    self.register_table[self.instructions_to_execute[instruction][0]]
                    is not None
                ):
                    # Check dest register to see whether it's busy or not
                    continue
                if fu["busy"]:
                    # F.U. is busy, try another one
                    continue
                fu["busy"] = True
                fu["op"] = instruction
                fu["fi"] = self.instructions_to_execute[instruction][0]
                fu["fj"] = self.instructions_to_execute[instruction][1]
                fu["fk"] = self.instructions_to_execute[instruction][2]
                if fu["fj"] is not None:
                    fu["qj"] = self.register_table[fu["fj"]]
                    if self.register_table[fu["fj"]] is not None:
                        fu["rj"] = 0
                    else:
                        fu["rj"] = 1
                if fu["fk"] is not None:
                    fu["qk"] = self.register_table[fu["fk"]]
                    if self.register_table[fu["fk"]] is not None:
                        fu["rk"] = 0
                    else:
                        fu["rk"] = 1
                self.instruction_table[instruction][
                    "issue"
                ] = lap  # lap that the stage has occured
                continue  # Take only one functional unit, of course

    def loop(self):
        lap = 1
        while True:
            self.issue_stage(lap)

            print(self.instruction_table)
            print(self.functional_unit_table)
            lap += 1
            if lap > 5:
                break


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_rel_path = "tests/data/test_1.txt"
    test_1_path = os.path.join(dir_path, file_rel_path)
    obj = ScoreboardingSIM(test_1_path)
    obj.execute()
    print(obj.instructions_to_execute)
