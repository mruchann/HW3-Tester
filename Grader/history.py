import enum

hist_student_file = None

class Action_Type(enum.Enum):
    none = "?"
    touch = "touch"
    mkdir = "mkdir"
    rm = "rm"
    rmdir = "rmdir"
    mv = "mv"


class Action:
    def __init__(self, action_line: str):
        split_line = action_line.strip("\n").split(" ")
        if split_line[0] == "?":
            self.time = -1
        else:
            self.time = int(split_line[0])

        try:
            self.action_type = Action_Type(split_line[1])
        except Exception as e:
            print(e)
            self.action_type = Action_Type.none

        self.args = []
        self.dir_inodes = []
        self.inodes = []

        index = 2

        if split_line[index].endswith("]"):
            self.args.append(split_line[index].lstrip("[").rstrip("]"))
            index += 1
        else:
            self.args.append(split_line[index].lstrip("["))
            self.args.append(split_line[index + 1].rstrip("]"))
            index += 2

        if split_line[index].endswith("]"):
            temp = split_line[index].lstrip("[").rstrip("]")
            if temp == "?" or len(temp) == 0:
                self.dir_inodes.append(-1)
            else:
                self.dir_inodes.append(int(temp))
            index += 1
        else:
            temp = split_line[index].lstrip("[")
            if temp == "?":
                self.dir_inodes.append(-1)
            else:
                self.dir_inodes.append(int(temp))
            temp = split_line[index + 1].rstrip("]")
            if temp == "?":
                self.dir_inodes.append(-1)
            else:
                self.dir_inodes.append(int(temp))
            index += 2


        if split_line[index].endswith("]"):
            temp = split_line[index].lstrip("[").rstrip("]")
            if temp == "?":
                self.inodes.append(-1)
            else:
                self.inodes.append(int(temp))
            index += 1
        else:
            temp = split_line[index].lstrip("[")
            if temp == "?":
                self.inodes.append(-1)
            else:
                self.inodes.append(int(temp))
            temp = split_line[index + 1].rstrip("]")
            if temp == "?":
                self.inodes.append(-1)
            else:
                self.inodes.append(int(temp))
            index += 2

    def create_empty(self) -> __init__:
        if self.action_type == Action_Type.mv:
            return Action("? ? [? ?] [? ?] [?]")
        else:
            return Action("? ? [?] [?] [?]")

    def describes(self, other: __init__) -> bool:
        if len(other.args) > 2 or len(other.dir_inodes) > 2 or len(other.inodes) > 1:
            return False

        if other.action_type != Action_Type.none and other.action_type != Action_Type.mv:
            if len(other.args) > 1 or len(other.dir_inodes) > 1 or len(other.inodes) > 1:
                return False

        if other.time != -1 and other.time != self.time:
            return False

        if other.action_type != Action_Type.none and other.action_type != self.action_type:
            return False

        for arg in other.args:
            if arg != "?" and arg not in self.args:
                return False

        if self.action_type == Action_Type.mv and len(other.args) == 2:
            if other.args[0] != "?" and other.args[0] != self.args[0]:
                return False
            if other.args[1] != "?" and other.args[1] != self.args[1]:
                return False

        for inode in other.dir_inodes:
            if inode != -1 and inode not in self.dir_inodes:
                return False

        for inode in other.inodes:
            if inode != -1 and inode not in self.inodes:
                return False

        return True

    def complements(self, other: __init__) -> bool:
        if self.time == -1 and other.time != -1:
            return True

        if self.action_type == Action_Type.none and other.action_type != Action_Type.none:
            return True

        for arg in other.args:
            if arg != "?" and arg not in self.args:
                return True

        for inode in other.dir_inodes:
            if inode != -1 and inode not in self.dir_inodes:
                return True

        for inode in other.inodes:
            if inode != -1 and inode not in self.inodes:
                return True

        return False

    def combine(self, other: __init__):
        if self.time == -1 and other.time != -1:
            self.time = other.time

        if self.action_type == Action_Type.none and other.action_type != Action_Type.none:
            self.action_type = other.action_type

        for i in range(min(len(other.args), len(self.args))):
            if other.args[i] != "?" and self.args[i] == "?":
                self.args[i] = other.args[i]

        for inode in other.dir_inodes:
            if inode != -1 and inode not in self.dir_inodes:
                for i in range(len(self.dir_inodes)):
                    if self.dir_inodes[i] == -1:
                        self.dir_inodes[i] = inode
                        break

        for inode in other.inodes:
            if inode != -1 and inode not in self.inodes:
                for i in range(len(self.inodes)):
                    if self.inodes[i] == -1:
                        self.inodes[i] = inode
                        break

    def count_completed(self) -> int:
        retval = 0
        if self.action_type != Action_Type.none:
            retval += 1
        if self.time != -1:
            retval += 1
        for arg in self.args:
            if arg != "?":
                retval += 1
        for inode in self.dir_inodes:
            if inode != -1:
                retval += 1
        for inode in self.inodes:
            if inode != -1:
                retval += 1
        return retval


class History:
    def __init__(self, truth_file: str):
        with open(truth_file) as file:
            lines = file.readlines()
        self.true_actions: dict[int, Action] = {}
        self.recovered_actions: dict[int, Action] = {}

        for line in lines:
            action = Action(line)
            self.true_actions[action.time] = action
            self.recovered_actions[action.time] = action.create_empty()

    def add_action(self, action: Action) -> bool:
        if action.time != -1:
            if action.time in self.true_actions.keys():
                if self.true_actions[action.time].describes(action) and self.recovered_actions[action.time].complements(action):
                    self.recovered_actions[action.time].combine(action)
                    return True
                else:
                    return False
            else:
                return False

        for time in sorted(self.true_actions.keys()):
            if self.true_actions[time].describes(action) and self.recovered_actions[time].complements(action):
                self.recovered_actions[time].combine(action)
                return True

        return False

    def parse_history_output(self, output_path) -> int:
        errors = 0
        with open(output_path) as file:
            try:
                lines = file.readlines()
            except Exception as e:
                print(e)
                if hist_student_file != None:
                    hist_student_file.write(f"{str(e)}\n")
                return self.get_true_count()
        for line in list(lines):
            if len(line.strip("\n")) == 0:
                lines.remove(line)
            if line.count("[") != 3 or line.count("]") != 3:
                lines.remove(line)
                print(f"Error (Format): {line.strip()}")
                if hist_student_file != None:
                    hist_student_file.write(f"Error (Format): {line.strip()}\n")
                errors += 1
            elif not line.startswith("?"):
                action = Action(line)
                retval = self.add_action(action)
                if not retval:
                    print(f"Error (Matching): {line.strip()}")
                    if hist_student_file != None:
                        hist_student_file.write(f"Error (Matching): {line.strip()}\n")
                    errors += max(1, action.count_completed())
                lines.remove(line)
        for line in lines:
            action = Action(line)
            retval = self.add_action(action)
            if not retval:
                if hist_student_file != None:
                    hist_student_file.write(f"Error (Matching): {line.strip()}\n")
                print(f"Error (Matching): {line.strip()}")
                errors += max(1, action.count_completed())
        return errors

    def get_completion_count(self):
        retval = 0
        for action in self.recovered_actions.values():
            retval += action.count_completed()
        return retval
        
    def get_true_count(self):
        retval = 0
        for action in self.true_actions.values():
            retval += action.count_completed()
        return retval


def compare_histories(student_output: str, history_truth: str, possible_truth: str):
    hist1 = History(history_truth)
    errors1 = hist1.parse_history_output(possible_truth)
    if errors1 != 0:
        print(f"Possible Truth is Flawed: {errors1}")
    count1 = hist1.get_completion_count()

    hist2 = History(history_truth)
    errors2 = hist2.parse_history_output(student_output)
    count2 = hist2.get_completion_count()

    return count1, errors1, count2, errors2

