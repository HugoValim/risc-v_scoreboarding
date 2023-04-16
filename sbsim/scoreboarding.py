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
                        instructions_to_execute[instruction_with_index].append(None)

            return functional_units_config, instructions_to_execute

    def build_instruction_status(self) -> None:
        """Build instruction table based in the inputed instructions"""
        self.instruction_table = {}
        stages = ["issue", "read", "ex", "write", "processed", "finished"]
        instructions = [i for i in self.instructions_to_execute.keys()]
        for instruction in instructions:
            self.instruction_table[instruction] = {}
            for i in stages:
                self.instruction_table[instruction][i] = None

    def build_functional_unit_status(self) -> None:
        """Build functional unit table based in the inputed Functional Units"""
        self.functional_unit_table = {}
        self.functional_unit_elements = {
            "busy": None,
            "op": None,
            "fi": None,
            "fj": None,
            "fk": None,
            "qj": None,
            "qk": None,
            "rj": None,
            "rk": None,
            "reserved_by": None,
            "n_units": 0,
            "n_cycles": 0,
            "done_cycles": 0,
            "finished": None,
        }
        for fu in self.functional_units_config.keys():
            self.functional_unit_table[fu] = []
            for i in range(self.functional_units_config[fu]["n_units"]):
                dict_now = self.functional_unit_elements.copy()
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
        self.build_instruction_status()
        self.build_functional_unit_status()
        self.build_register_status()

    def issue_stage(self, lap: int):
        """Process the issue stage, making the needed check, basically the required F.U. mustn't busy and the dest register must no be free (avoiding WAW hazard)"""
        issue_done_this_lap = False
        previous_instruction_stage_status = True
        for instruction in self.instruction_table:
            if previous_instruction_stage_status is None:
                break  # Issue must be done in order
            if self.instruction_table[instruction]["issue"] is not None:
                #  Issue already occured, skip this one
                continue
            if issue_done_this_lap:
                break
            for idx, fu in enumerate(
                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ]
            ):
                if (
                    self.register_table[self.instructions_to_execute[instruction][0]]
                    is not None
                ):
                    # Check dest register to see whether it's busy or not
                    continue
                if fu["busy"]:
                    # F.U. is busy, try another one
                    continue
                # Update register table
                self.register_table[
                    self.instructions_to_execute[instruction][0]
                ] = instruction

                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ][idx]["busy"] = True
                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ][idx]["op"] = instruction
                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ][idx]["fi"] = self.instructions_to_execute[instruction][0]
                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ][idx]["fj"] = self.instructions_to_execute[instruction][1]
                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ][idx]["fk"] = self.instructions_to_execute[instruction][2]
                if fu["fj"] is not None:
                    self.functional_unit_table[
                        self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                    ][idx]["qj"] = self.register_table[fu["fj"]]
                    print(
                        self.functional_unit_table[
                            self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                        ][idx]["qj"]
                    )
                    if self.register_table[fu["fj"]] is not None:
                        self.functional_unit_table[
                            self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                        ][idx]["rj"] = 0
                    else:
                        self.functional_unit_table[
                            self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                        ][idx]["rj"] = 1
                else:
                    self.functional_unit_table[
                        self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                    ][idx]["rj"] = 1
                if fu["fk"] is not None:
                    self.functional_unit_table[
                        self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                    ][idx]["qk"] = self.register_table[fu["fk"]]
                    if self.register_table[fu["fk"]] is not None:
                        self.functional_unit_table[
                            self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                        ][idx]["rk"] = 0
                    else:
                        self.functional_unit_table[
                            self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                        ][idx]["rk"] = 1
                else:
                    self.functional_unit_table[
                        self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                    ][idx]["rk"] = 1
                self.instruction_table[instruction][
                    "issue"
                ] = lap  # lap that the stage has occured
                self.instruction_table[instruction]["processed"] = True
                self.functional_unit_table[
                    self.OPCODE_MAP[self.remove_instruction_idx(instruction)]
                ][idx]["reserved_by"] = instruction
                issue_done_this_lap = True
                break  # Take only one functional unit, of course
            previous_instruction_stage_status = self.instruction_table[instruction][
                "issue"
            ]  # Store previous state

    def read_stage(self, lap: int) -> None:
        """Process the read stage. Check if rk and rj are both 1, and make the reading if so"""
        for fu in self.functional_unit_table.keys():
            for fu_unit in self.functional_unit_table[fu]:
                if fu_unit["rj"] == 1 and fu_unit["rk"] == 1:
                    if self.instruction_table[fu_unit["reserved_by"]]["processed"]:
                        continue  # An action already occured in thsi instruction in this lap
                    self.instruction_table[fu_unit["reserved_by"]]["read"] = lap
                    fu_unit["rj"] = 0
                    fu_unit["rk"] = 0

    def execute_stage(self, lap: int) -> None:
        """Process the execution stage. Check the number of cycles needed for each F.U. and keep executing until reach this number of cycles"""
        for fu in self.functional_unit_table.keys():
            for fu_unit in self.functional_unit_table[fu]:
                if fu_unit["reserved_by"] is None:
                    continue  # This F.U. is not being used
                if self.instruction_table[fu_unit["reserved_by"]]["processed"]:
                    continue  # An action already occured in this instruction in this lap
                if fu_unit["finished"]:
                    continue  # Already fininished this unit
                self.instruction_table[fu_unit["reserved_by"]]["ex"] = lap
                if fu_unit["done_cycles"] == fu_unit["n_cycles"]:
                    fu_unit["finished"] = True
                fu_unit["done_cycles"] += 1
                self.instruction_table[fu_unit["reserved_by"]]["processed"] = True

    def write_stage(self, lap: int) -> None:
        """Process the write stage. Checks to see if the value calculated in the execute stage can be written (Avoid WAR hazard)."""

        def check_source_register(reg: str) -> bool:
            """Method to check if a destination register is source for a instruction"""
            for fu in self.functional_unit_table.keys():
                for fu_unit in self.functional_unit_table[fu]:
                    if reg == fu_unit["qj"] and fu_unit["rj"] == 1:
                        return False
                    if reg == fu_unit["qk"] and fu_unit["rk"] == 1:
                        return False
            return True

        def update_source_registers(reg: str) -> None:
            """Update the source register, sending the message that the source operand is now available"""
            for fus in self.functional_unit_table.values():
                for fu_unit in fus:
                    if reg == fu_unit["qj"]:
                        fu_unit["rj"] == 1
                    if reg == fu_unit["qk"]:
                        fu_unit["rk"] == 1

        for fu in self.functional_unit_table.keys():
            for idx, fu_unit in enumerate(self.functional_unit_table[fu]):
                if fu_unit["reserved_by"] is None:
                    continue  # This F.U. is not being used
                if not fu_unit["finished"]:
                    continue  # This F.U. is not ready
                if self.instruction_table[fu_unit["reserved_by"]]["processed"]:
                    continue  # An action already occured in this instruction in this lap
                if check_source_register(fu_unit["fi"]):
                    update_source_registers(fu_unit["fi"])
                    self.register_table[
                        self.instructions_to_execute[fu_unit["reserved_by"]][0]
                    ] = None
                    self.instruction_table[fu_unit["reserved_by"]]["write"] = lap
                    self.instruction_table[fu_unit["reserved_by"]]["finished"] = True
                    dict_now = self.functional_unit_elements.copy()
                    fu_unit = dict_now
                    self.functional_unit_table[fu][idx] = fu_unit

    def reset_state_to_next_lap(self):
        """Reset needed states to begin a new cycle"""
        for instruction in self.instruction_table.values():
            instruction["processed"] = False

    def check_if_pipeline_is_finished(self):
        for instruction in self.instruction_table.values():
            if not instruction["finished"]:
                return True
        return False

    def loop(self):
        lap = 1
        while self.check_if_pipeline_is_finished():
            self.issue_stage(lap)
            self.read_stage(lap)
            self.execute_stage(lap)
            self.write_stage(lap)
            self.reset_state_to_next_lap()
            print(self.register_table)
            lap += 1
            # print(lap)
            # if lap > 15:
            #     break

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
