import os
from dataclasses import dataclass

import pandas as pd
import numpy as np


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

    def __init__(self, file_paths: list[os.path], print_each_stage: bool) -> None:
        self.files = file_paths
        self.print_each_stage = print_each_stage

    def execute(self):
        """Method to execute the simulator"""
        file_data = self.get_inputed_files_data()
        self.functional_units_config, self.instructions_to_execute = self.parse_file(
            file_data
        )
        self.build_status()
        self.loop()
        if not self.print_each_stage:
            print(self.build_table_from_array())

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
    def remove_instruction_idx(instruction: str) -> str:
        """Get only the raw name of the instruction without its index"""
        return instruction.split("_")[0]

    def get_fu_from_inst(self, instruction: str) -> str:
        """Get the functional unit for the given instruction"""
        return self.OPCODE_MAP[self.remove_instruction_idx(instruction)]

    def get_inputed_files_data(self) -> list:
        """Get the data in the inputed files and return a list with all information"""
        data = []
        for file in self.files:
            with open(file, "r") as f:
                for line in f:
                    striped_line = line.strip()
                    if not striped_line:  # Skip blank lines
                        continue
                    data.append(striped_line)
        return data

    def parse_file(self, file_data: str) -> tuple[dict, dict]:
        """Parse inputed file and build functional units and instructions config"""
        functional_units_config = {}
        instructions_to_execute = {}
        for info in file_data:
            fields = info.replace(",", " ").split()
            if fields[0].lower() in self.FUNCTIONAL_UNITS:
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
                        instructions_to_execute[instruction_with_index].insert(0, None)
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
        stages = [
            "issue",
            "read",
            "ex",
            "write",
            "processed",
            "finished",
            "issue_state",
            "read_state",
            "ex_state",
            "write_state",
        ]
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
            self.register_table[self.REG_PREFIXES["int"] + str(i)] = None
        for i in range(regf):
            self.register_table[self.REG_PREFIXES["float"] + str(i)] = None

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
        if self.instruction_before_issue_state != "done":
            return
        if self.issue_done_flag:
            return
        if self.instruction_table[instruction]["issue_state"] == "done":
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
            self.instruction_table[instruction]["issue_state"] = "done"
            self.instruction_table[instruction]["processed"] = True

            # Set the flag to tell that one instruction already issued this cycle
            self.issue_done_flag = True
            break

    def read_stage(self, cycle: int, instruction: str) -> None:
        """Process the read stage. Check if rk and rj are both 1, and make the reading if so"""
        raw_functional_unit = self.get_fu_from_inst(instruction)
        if self.instruction_table[instruction]["issue_state"] != "done":
            #  Issue didn't even occured yet
            return
        if self.instruction_table[instruction]["read_state"] == "done":
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
            self.instruction_table[instruction]["read_state"] = "done"

    def execute_stage(self, cycle: int, instruction: str) -> None:
        """Process the execution stage. Check the number of cycles needed for each F.U. and keep executing until reach this number of cycles"""
        raw_functional_unit = self.get_fu_from_inst(instruction)
        if self.instruction_table[instruction]["read_state"] != "done":
            #  Issue didn't even occured yet
            return
        if self.instruction_table[instruction]["ex_state"] == "done":
            #  Read already occured, skip this one
            return
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
            self.instruction_table[instruction]["ex"] = cycle
            self.instruction_table[instruction]["processed"] = True

            # Update functional unit table
            self.functional_unit_table[raw_functional_unit][idx]["done_cycles"] += 1
            if fu["done_cycles"] == fu["n_cycles"]:
                self.functional_unit_table[raw_functional_unit][idx]["finished"] = True
                self.instruction_table[instruction]["ex_state"] = "done"

    def write_stage(self, cycle: int, instruction: str) -> None:
        """Process the write stage. Checks to see if the value calculated in the execute stage can be written (Avoid WAR hazard)."""
        dest_register_idx = 0
        raw_functional_unit = self.get_fu_from_inst(instruction)
        dest_register = self.instructions_to_execute[instruction][dest_register_idx]

        if self.instruction_table[instruction]["ex_state"] != "done":
            #  Ex didn't even occured yet
            return
        if self.instruction_table[instruction]["write_state"] == "done":
            #  Read already occured, skip this one
            return

        def check_source_register(reg: str) -> bool:
            """Method to check if a destination register is source for a instruction, return true if it can proceed"""
            for fu in self.functional_unit_table.keys():
                for fu_unit in self.functional_unit_table[fu]:
                    if reg == fu_unit["qj"] and fu_unit["rj"] == 1:
                        return False
                    if reg == fu_unit["qk"] and fu_unit["rk"] == 1:
                        return False
            return True

        if self.instruction_table[instruction]["processed"]:
            # This instruction already processed this cycle
            return
        if not check_source_register(dest_register):
            return

        for idx, fu in enumerate(self.functional_unit_table[raw_functional_unit]):
            if instruction != fu["reserved_by"]:
                # Not the unit that is being used by this instruction
                continue
            if not fu["finished"]:
                # Execute not finished yet
                return
            self.reset_fu.append((raw_functional_unit, idx))

        # Interact with register table
        self.registers_to_update.append((dest_register, instruction))

        # Update instruction table:
        self.instruction_table[instruction]["write"] = cycle
        self.instruction_table[instruction]["write_status"] = "done"
        self.instruction_table[instruction]["finished"] = True

    def update_source_registers(self) -> None:
        """Update the source register, sending the message that the source operand is now available"""
        for reg in self.registers_to_update:
            self.register_table[reg[0]] = None  # Register is not reserved anymore
            for fu in self.functional_unit_table.keys():
                for idx, fu_unit in enumerate(self.functional_unit_table[fu]):
                    if reg[1] == fu_unit["qj"]:
                        self.functional_unit_table[fu][idx]["rj"] = 1
                    if reg[1] == fu_unit["qk"]:
                        self.functional_unit_table[fu][idx]["rk"] = 1

    def reset_state_to_next_cycle(self):
        """Reset needed states to begin a new cycle"""
        self.issue_done_flag = False
        self.registers_to_update = []
        default_functional_unit_table = self.build_functional_unit_status()
        for fu in self.reset_fu:
            self.functional_unit_table[fu[0]][fu[1]] = default_functional_unit_table[
                fu[0]
            ][fu[1]]
        for instruction in self.instruction_table.values():
            instruction["processed"] = False
        self.reset_fu = []

    def check_if_pipeline_is_finished(self):
        for instruction in self.instruction_table.values():
            if not instruction["finished"]:
                return True
        return False

    def loop(self):
        self.issue_done_flag = False
        self.instruction_before_issue_state = "done"
        self.registers_to_update = []
        self.reset_fu = []
        cycle = 1
        while self.check_if_pipeline_is_finished():
            for instruction in self.instruction_table.keys():
                if self.instruction_table[instruction]["finished"]:
                    self.instruction_before_issue_state = self.instruction_table[
                        instruction
                    ]["issue_state"]
                    continue
                self.issue_stage(cycle, instruction)
                self.read_stage(cycle, instruction)
                self.execute_stage(cycle, instruction)
                self.write_stage(cycle, instruction)
                self.instruction_before_issue_state = self.instruction_table[
                    instruction
                ]["issue_state"]

            self.update_source_registers()
            self.reset_state_to_next_cycle()
            if self.print_each_stage:
                print(self.build_table_from_array())
            cycle += 1

    def build_table_from_array(self) -> pd.DataFrame:
        """Build a pandas DtaFrame form an array"""
        instructions = [i for i in self.instructions_to_execute.keys()]
        table = {"instruction": instructions}
        stages = {"issue": [], "read": [], "ex": [], "write": []}
        for instruction in instructions:
            for stage in stages.keys():
                stages[stage].append(str(self.instruction_table[instruction][stage]))
        table_stages = {stage: stages[stage] for stage in stages}
        table.update(table_stages)
        return pd.DataFrame(table)


def main() -> None:
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # First test
    test_1_path = "tests/data/test_1.txt"
    test_1_path = os.path.join(dir_path, test_1_path)
    obj = ScoreboardingSIM([test_1_path], False)
    obj.execute()

    # Second test
    test_2a_path = "tests/data/test_2_a.txt"
    test_2b_path = "tests/data/test_2_b.txt"
    test_2a_path = os.path.join(dir_path, test_2a_path)
    test_2b_path = os.path.join(dir_path, test_2b_path)
    obj = ScoreboardingSIM([test_2a_path, test_2b_path], False)
    obj.execute()

    # Third
    test_3a_path = "tests/data/test_3_a.txt"
    test_3b_path = "tests/data/test_3_b.txt"
    test_3a_path = os.path.join(dir_path, test_3a_path)
    test_3b_path = os.path.join(dir_path, test_3b_path)
    obj = ScoreboardingSIM([test_3a_path, test_3b_path], False)
    obj.execute()


if __name__ == "__main__":
    main()
