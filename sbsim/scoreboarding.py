import os
from dataclasses import dataclass

import pandas as pd


class ScoreboardingSIM:

    FUNCTIONAL_UNITS = ["int", "mult", "add", "div"]

    OPCODE_MAP = {
        "ild": "int",
        "fld": "int",
        "isw": "int",
        "fsd": "int",
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
        self.functional_units_config, self.instructions_to_execute = self.parse_file()
        self.build_status()
        self.loop()

    @staticmethod
    def add_prefix_to_instructions(
        instruction_now: str, current_instructions: dict
    ) -> str:
        """Add a prefix to every instruction to indentify different ones in the execution"""
        start_idx = 1
        prefix = "_"
        for instruction in current_instructions.keys():
            if instruction_now == instruction.split("_")[0]:
                start_idx += 1
        instruction_idx = instruction_now + prefix + str(start_idx)
        return instruction_idx

    @staticmethod
    def remove_instruction_idx(instruction: str):
        """Get only the raw name of the instruction without its index"""
        return instruction.split("_")[0]

    def get_fu_from_inst(self, instruction: str) -> str:
        """Get the functional unit for the given instruction"""
        return self.OPCODE_MAP[self.remove_instruction_idx(instruction)]

    def parse_file(self) -> tuple[dict, dict]:
        """Parse inputed file and build functional units and instructions config"""
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
                        if "sd" in instruction_with_index:
                            instructions_to_execute[instruction_with_index].insert(
                                0, None
                            )
                        else:
                            instructions_to_execute[instruction_with_index].append(None)

            return functional_units_config, instructions_to_execute

    def build_status(self):
        """Build all needed status table"""
        self.build_instruction_status()
        self.functional_unit_table = self.build_functional_unit_status()
        self.build_register_status()

    def build_instruction_status(self) -> None:
        """Build instruction table based in the inputed instructions"""
        self.instruction_table = {}
        stages = ["issue", "read", "ex", "write", "processed", "finished"]
        instructions = [i for i in self.instructions_to_execute.keys()]
        for instruction in instructions:
            self.instruction_table[instruction] = {}
            for i in stages:
                self.instruction_table[instruction][i] = None

    def create_default_fu(self):
        return_value = {}
        functional_unit_elements = [
            "busy",
            "op",
            "fi",
            "fj",
            "fk",
            "qj",
            "qk",
            "rj",
            "rk",
            "reserved_by",
            "n_cycles",
            "done_cycles",
            "finished",
        ]
        for i in functional_unit_elements:
            return_value[i] = None
        return return_value

    def build_functional_unit_status(self) -> None:
        """Build functional unit table based in the inputed Functional Units"""
        functional_unit_table = {}
        for fu in self.functional_units_config.keys():
            functional_unit_table[fu] = []
            for i in range(self.functional_units_config[fu]["n_units"]):
                functional_unit_table[fu].append(self.create_default_fu())
                functional_unit_table[fu][i]["n_cycles"] = self.functional_units_config[
                    fu
                ]["n_cycles"]
                functional_unit_table[fu][i]["done_cycles"] = 0
        return functional_unit_table

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

    def issue_stage(self, cycle: int, instruction: str) -> None:
        """Process the issue stage, making the needed check, basically the required F.U. mustn't busy and the dest register must no be free (avoiding WAW hazard)"""
        dest_register_idx = 0
        source_register_1_idx = 1
        source_register_2_idx = 2
        dest_register = self.instructions_to_execute[instruction][dest_register_idx]
        source_register_1 = self.instructions_to_execute[instruction][
            source_register_1_idx
        ]
        source_register_2 = self.instructions_to_execute[instruction][
            source_register_2_idx
        ]
        raw_functional_unit = self.get_fu_from_inst(instruction)
        if self.issue_done_flag:
            return
        if self.instruction_table[instruction]["issue"] is not None:
            #  Issue already occured, skip this one
            return
        if dest_register is not None:
            if self.register_table[dest_register] is not None:
                #  Dest register is busy
                self.issue_done_flag = True
                return
        for idx, fu in enumerate(self.functional_unit_table[raw_functional_unit]):
            if fu["busy"]:
                # Functional Unit already in use
                continue
            # All checks done, now we can issu o/

            # Now the functional Unit table
            self.functional_unit_table[raw_functional_unit][idx][
                "reserved_by"
            ] = instruction
            self.functional_unit_table[raw_functional_unit][idx]["busy"] = True
            self.functional_unit_table[raw_functional_unit][idx][
                "op"
            ] = self.remove_instruction_idx(instruction)
            self.functional_unit_table[raw_functional_unit][idx]["fi"] = dest_register
            self.functional_unit_table[raw_functional_unit][idx][
                "fj"
            ] = source_register_1
            self.functional_unit_table[raw_functional_unit][idx][
                "fk"
            ] = source_register_2
            self.functional_unit_table[raw_functional_unit][idx][
                "qj"
            ] = self.register_table[source_register_1]
            if self.register_table[source_register_1] is not None:
                self.functional_unit_table[raw_functional_unit][idx]["rj"] = 0
            else:
                self.functional_unit_table[raw_functional_unit][idx]["rj"] = 1
            if self.functional_unit_table[raw_functional_unit][idx]["fk"] is not None:
                self.functional_unit_table[raw_functional_unit][idx][
                    "qk"
                ] = self.register_table[source_register_2]
                if self.register_table[source_register_2] is not None:
                    self.functional_unit_table[raw_functional_unit][idx]["rk"] = 0
                else:
                    self.functional_unit_table[raw_functional_unit][idx]["rk"] = 1
            else:
                self.functional_unit_table[raw_functional_unit][idx]["rk"] = 1

            # Request the dest register in register table
            if dest_register is not None:
                self.register_table[dest_register] = instruction

            # Instruction table
            self.instruction_table[instruction]["issue"] = cycle
            self.instruction_table[instruction]["processed"] = True

            # Set the flag to tell that one instruction already issued this cycle
            self.issue_done_flag = True

    def read_stage(self, cycle: int, instruction: str) -> None:
        """Process the read stage. Check if rk and rj are both 1, and make the reading if so"""
        raw_functional_unit = self.get_fu_from_inst(instruction)
        if self.instruction_table[instruction]["read"] is not None:
            #  Read already occured, skip this one
            return
        if self.instruction_table[instruction]["processed"]:
            # This instruction already processed this cycle
            return
        for idx, fu in enumerate(self.functional_unit_table[raw_functional_unit]):
            if instruction != fu["reserved_by"]:
                # Not the unit that is being used by this instruction
                continue
            if fu["rj"] != 1 or fu["rk"] != 1:
                self.instruction_table[instruction]["processed"] = True
                break
            # If we reached here, everything is fine and we can read

            # Update functional unit table
            self.functional_unit_table[raw_functional_unit][idx]["rj"] = 0
            self.functional_unit_table[raw_functional_unit][idx]["rk"] = 0

            # Update instruction table
            self.instruction_table[instruction]["processed"] = True
            self.instruction_table[instruction]["read"] = cycle

    def execute_stage(self, cycle: int, instruction: str) -> None:
        """Process the execution stage. Check the number of cycles needed for each F.U. and keep executing until reach this number of cycles"""
        raw_functional_unit = self.get_fu_from_inst(instruction)
        if self.instruction_table[instruction]["processed"]:
            # This instruction already processed this cycle
            return
        for idx, fu in enumerate(self.functional_unit_table[raw_functional_unit]):
            if instruction != fu["reserved_by"]:
                # Not the unit that is being used by this instruction
                continue
            if fu["finished"]:
                # Already fininished this unit
                continue
            # If we reached here, everything is fine and we can execute
            # Update instruction table:
            print("Heree")
            self.instruction_table[instruction]["ex"] = cycle
            self.instruction_table[instruction]["processed"] = True

            # Update functional unit table
            self.functional_unit_table[raw_functional_unit][idx]["done_cycles"] += 1
            if fu["done_cycles"] == fu["n_cycles"]:
                self.functional_unit_table[raw_functional_unit][idx]["finished"] = True

    def write_stage(self, cycle: int) -> None:
        """Process the write stage. Checks to see if the value calculated in the execute stage can be written (Avoid WAR hazard)."""
        pass

    def reset_state_to_next_cycle(self):
        """Reset needed states to begin a new cycle"""
        self.issue_done_flag = False
        for instruction in self.instruction_table.values():
            instruction["processed"] = False

    def check_if_pipeline_is_finished(self):
        for instruction in self.instruction_table.values():
            if not instruction["finished"]:
                return True
        return False

    def loop(self):
        self.issue_done_flag = False
        cycle = 1
        while self.check_if_pipeline_is_finished():
            for instruction in self.instruction_table.keys():
                self.issue_stage(cycle, instruction)
                self.read_stage(cycle, instruction)
                self.execute_stage(cycle, instruction)
                # self.write_stage(cycle, instruction)
            self.reset_state_to_next_cycle()
            cycle += 1
            # print(cycle)
            if cycle > 10:
                break

    def build_table_from_array(self) -> pd.DataFrame:
        """Build a pandas DtaFrame form an array"""
        stages = ["issue", "read", "ex", "write", "processed"]
        instructions = [i for i in self.instructions_to_execute.keys()]
        initialize_w_none = [None for i in range(len(instructions))]
        table = {"instruction": instructions}
        table_stages = {stage: initialize_w_none for stage in stages}
        table.update(table_stages)
        return pd.DataFrame(table)


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_rel_path = "tests/data/test_1.txt"
    test_1_path = os.path.join(dir_path, file_rel_path)
    obj = ScoreboardingSIM(test_1_path)
    obj.execute()
    print(obj.instructions_to_execute)
    print(obj.instruction_table)
    print(obj.functional_unit_table)
    print(obj.register_table)
