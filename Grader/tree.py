tree_student_file = None

class Node:
    def __init__(self, name: str):
        self.name = name
        self.content: dict[str, Node] = {}
        self.is_ghost = name.startswith("(") and name.endswith(")")

    def append(self, node: __init__):
        self.content[node.name] = node

    def print(self, level: int = 0):
        print(f"{'-' * (level + 1)} {self.name}")
        for content in self.content:
            self.content[content].print(level + 1)

    def count(self, count_ghost: bool = False):
        retval = 1
        for content in self.content:
            if ((count_ghost and self.content[content].is_ghost) or (not self.content[content].is_ghost)) and self.content != self:
                retval += self.content[content].count(count_ghost)
        return retval

    def compare(self, node: __init__, compare_ghost: bool = False):
        retval = 0
        for content in self.content:
            if (compare_ghost and self.content[content].is_ghost) or (not self.content[content].is_ghost):
                if content in node.content:
                    retval += self.content[content].compare(node.content[content], compare_ghost)
                else:
                    retval += self.content[content].count(compare_ghost)
        return retval


class Tree:
    def __init__(self, filename: str):
        file = open(filename, "r")
        lines = file.readlines()
        file.close()
        last_nodes: list[Node] = []
        first_node = True
        for line in lines:
            if line.startswith("-"):
                prefix, name = line.strip("\n").split(" ", 1)
                if len(prefix) != prefix.count("-"):
                    if tree_student_file != None:
                        tree_student_file.write(f"prefix contains foreign characters: {prefix}\n")
                    print(f"prefix contains foreign characters: {prefix}")
                level = len(prefix) - 1
                node = Node(name)
                if first_node:
                    if level != 0:
                        if tree_student_file != None:
                            tree_student_file.write(f"Wrong initial level: {level}\n")
                        print(f"Wrong initial level: {level}")
                        return
                    first_node = False
                if level == 0:
                    if len(last_nodes) > 0:
                        if tree_student_file != None:
                            tree_student_file.write(f"Root is overwritten: {last_nodes[0].name} -> {node.name}\n")
                        print(f"Root is overwritten: {last_nodes[0].name} -> {node.name}")
                    last_nodes.append(node)
                elif len(last_nodes) <= level:
                    last_nodes.append(node)
                    last_nodes[level - 1].append(node)
                else:
                    last_nodes[level] = node
                    last_nodes[level - 1].append(node)
        if len(last_nodes) > 0:
            self.root = last_nodes[0]
        else:
            self.root = None

    def print(self):
        if self.root is not None:
            self.root.print()
        else:
            print("")

    def count(self, count_ghost: bool = False):
        if self.root is not None:
            return self.root.count(count_ghost)
        else:
            return 0

    def compare(self, tree: __init__, compare_ghost: bool = False):
        count1 = self.count(compare_ghost)
        count2 = tree.count(compare_ghost)
        if count2 == 0:
            return 0, count1
        if count1 == 0:
            return 0, 0
        return self.root.compare(tree.root, compare_ghost), count1


def compare_trees(tree1_file_name: str, tree2_file_name: str, compare_ghost: bool = False):
    tree1 = Tree(tree1_file_name)
    tree2 = Tree(tree2_file_name)
    score1, count1 = tree1.compare(tree2, compare_ghost)
    score2, count2 = tree2.compare(tree1, compare_ghost)
    return score1, count1, score2, count2




