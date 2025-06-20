import history
import subprocess
import os
import tree
import shutil
import time
import csv

student_file = None

STUDENT_EXEC_NAME = "histext2fs"
STUDENT_TAR_NAME = "hw3.tar.gz"
IMAGE_FOLDER = os.path.abspath("./Testcases")
STUDENT_FOLDER = os.path.abspath("./Students")
GRADING_FOLDER = os.path.abspath("./Grades")
SUBMISSION_FOLDER = os.path.abspath("./Submission")


def get_tree_score(student_output: str, tree_truth: str):
    try:
        tree_difference1, tree_total1, tree_difference2, tree_total2 = tree.compare_trees(student_output, tree_truth, False)
        tree_difference_ghost1, tree_total_ghost1, tree_difference_ghost2, tree_total_ghost2 = tree.compare_trees(student_output, tree_truth, True)
    except Exception as e:
        print(e)
        if student_file != None:
            student_file.write(f"{str(e)}\n")
        return 0.0, 0.0
    tree_difference = tree_difference1 + tree_difference2
    total_tree = tree_total2

    tree_difference_ghost = tree_difference_ghost1 + tree_difference_ghost2 - tree_difference
    total_tree_ghost = tree_total_ghost2 - total_tree

    tree_score = max(1.0 - (float(tree_difference) / float(total_tree)), 0.0) * 100.0
    if tree_difference_ghost == 0:
        tree_score_ghost = 100.0
    elif total_tree_ghost == 0:
        tree_score_ghost = 0.0
    else:
        tree_score_ghost = max(1.0 - (float(tree_difference_ghost) / float(total_tree_ghost)), 0.0) * 100.0 if total_tree_ghost > 0 else 100.0

    return tree_score, tree_score_ghost


def get_history_score(student_output: str, history_truth: str, possible_truth: str):
    count1, errors1, count2, errors2 = history.compare_histories(student_output, history_truth, possible_truth)

    if errors2 >= count2:
        return 0.0

    return min(100.0, (120.0 / float(count1)) * float(count2 - errors2))


def compute_score(tree_output: str, hist_output: str, tree_truth: str, hist_truth: str, hist_possible: str):
    tree_score, tree_score_ghost = get_tree_score(tree_output, tree_truth)
    hist_score = get_history_score(hist_output, hist_truth, hist_possible)

    return tree_score * 0.2 + tree_score_ghost * 0.1 + hist_score * 0.7


def switch_dir(new_dir: str) -> str:
    current_directory = os.getcwd()
    os.chdir(new_dir)
    return current_directory


def run_subprocess(args):
    process = subprocess.run(args, capture_output=True)
    success = process.returncode == 0
    if not success:
        print(f"{process.args}")
        print(f"{process.returncode}\n")
        print(f"{process.stdout}\n")
        print(f"{process.stderr}\n")
    return success

testcases = {}

class TestCase:
    def __init__(self, name: str, image_location: str, history_truth_location: str, history_bench_location: str, state_truth_location: str):
        self.name = name
        self.im_loc = image_location
        self.hist_truth_loc = history_truth_location
        self.hist_bench_loc = history_bench_location
        self.state_truth_loc = state_truth_location
        testcases[self.name] = self

    def __str__(self):
        return f"{self.name}({self.im_loc}): {self.hist_bench_loc}/{self.hist_truth_loc} - {self.state_truth_loc}"


class TestCase_Grade:
    def __init__(self, testcase: str, student_hist: str, student_state: str, duration: float):
        if os.path.exists(student_state):
            self.state_score, self.ghost_score = get_tree_score(student_state, testcases[testcase].state_truth_loc)
        else:
            self.state_score = 0
            self.ghost_score = 0
            
        if os.path.exists(student_hist):
            count1, errors1, count2, errors2 = history.compare_histories(student_hist, testcases[testcase].hist_truth_loc, testcases[testcase].hist_bench_loc)
        else:
            count2 = 0
            errors2 = 0
        self.hist_count = count2
        self.hist_error = errors2

        self.hist_score = 0.0 if errors2 >= count2 else  min(100.0, (120.0 / float(count1)) * float(count2 - errors2))
        self.duration = duration

    def getDict(self, name: str):
        retval: dict[str, float | str | int] = {"testcase": name,
                                                "execution_time": self.duration,
                                                "execution_penalty": max(self.duration - 300.0, 0.0),
                                                "hist_count": self.hist_count,
                                                "hist_error": self.hist_error,
                                                "hist_score": self.hist_score,
                                                "state_score": self.state_score,
                                                "ghost_score": self.ghost_score
                                                }
        penalty = max(self.duration - 130.0, 0.0)

        retval["final_score"] = max(self.state_score * 0.2 + self.ghost_score * 0.1 + self.hist_score * 0.7 - penalty, 0.0)

        return retval


class Student:
    def __init__(self, folder_name: str):
        fields = folder_name.split("_")
        self.name = fields[0]
        self.student_id = fields[1]
        self.folder_name = folder_name
        self.grades: dict[str, TestCase_Grade] = {}
        self.successful = True

        self.check = 0
        self.perform_init()

    def perform_init(self):
        if self.check == 0:
            if not os.path.exists(f"{STUDENT_FOLDER}/{self.folder_name}/{STUDENT_TAR_NAME}"):
                print(f"No File {self.folder_name}/{STUDENT_TAR_NAME}")
                self.successful = False
                return
            self.check = 1

        current_directory = switch_dir(f"{STUDENT_FOLDER}/{self.folder_name}")
        if self.check == 1:
            if not run_subprocess(["tar", "-xf", STUDENT_TAR_NAME]):
                self.successful = False
                print(f"Uncompress failed for {self.name}-{self.student_id}")
                switch_dir(current_directory)
                return
            self.check = 2

        if self.check == 2:
            if not run_subprocess(["make", "all"]):
                self.successful = False
                print(f"Make failed for {self.name}-{self.student_id}")
                switch_dir(current_directory)
                return
            self.check = 3

        if self.check == 3:
            if not os.path.exists(STUDENT_EXEC_NAME):
                print(f"No File {self.folder_name}/{STUDENT_EXEC_NAME}")
                self.successful = False
                switch_dir(current_directory)
                return
            self.check = 4

        if self.check == 4:
            switch_dir(current_directory)
            self.successful = True

    def __str__(self):
        if self.successful:
            return f"{self.name} {self.student_id} {self.successful}"
        else:
            return f"{self.name} {self.student_id} {self.successful}: {self.check}"

    def save_as_csv(self, folder: str):
        with open(f"{folder}/{self.name}_{self.student_id}.csv", "w",  newline='') as file:
            fieldnames = ["testcase", "execution_time", "execution_penalty", "hist_count", "hist_error", "hist_score", "state_score", "ghost_score", "final_score"]
            writer = csv.DictWriter(file, fieldnames=fieldnames, dialect=csv.unix_dialect, restval="-")

            writer.writeheader()
            final_scores = {"testcase": "Total", "hist_score": 0.0, "state_score": 0.0,
                            "ghost_score": 0.0, "final_score": 0.0}

            for case in self.grades:
                case_dict = self.grades[case].getDict(case)
                writer.writerow(case_dict)

                final_scores["hist_score"] += case_dict["hist_score"]
                final_scores["state_score"] += case_dict["state_score"]
                final_scores["ghost_score"] += case_dict["ghost_score"]
                final_scores["final_score"] += case_dict["final_score"]

            final_scores["hist_score"] /= len(self.grades)
            final_scores["state_score"] /= len(self.grades)
            final_scores["ghost_score"] /= len(self.grades)
            final_scores["final_score"] /= len(self.grades)

            writer.writerow(final_scores)


students = []
testcase_names = ["testcase1", "testcase2", "testcase3", "testcase4", "testcase5", "testcase6", "testcase7", "testcase8", "testcase9", "testcase10"]

def init_testcases():
    for testcase in testcase_names:
        TestCase(testcase,
                 f"{IMAGE_FOLDER}/{testcase}/{testcase}.img",
                 f"{IMAGE_FOLDER}/{testcase}/{testcase}_hist_truth.txt",
                 f"{IMAGE_FOLDER}/{testcase}/{testcase}_hist_bench.txt",
                 f"{IMAGE_FOLDER}/{testcase}/{testcase}_state_truth.txt")



def init_students():
    student_folder = os.listdir(STUDENT_FOLDER)
    for folder in student_folder:
        students.append(Student(folder))


def perform_test(student: Student, case: TestCase):
    print(case.name)
    if student_file != None:
        student_file.write(f"{case.name}\n")
    student_absolute_folder = f"{STUDENT_FOLDER}/{student.folder_name}"
    case_folder = f"{student_absolute_folder}/{case.name}"
    im_name = shutil.copy(case.im_loc, f"{student_absolute_folder}/")
    current_directory = switch_dir(student_absolute_folder)
    now = time.time()
    try:
        process = subprocess.run(f'./{STUDENT_EXEC_NAME} {case.name}.img {case.name}_state.txt {case.name}_hist.txt', shell=True, capture_output=True, timeout=230)
        with open(f"{case.name}_output.txt", "wb") as file:
            file.write(process.stdout)
        shutil.copy(f"{case.name}_state.txt", f"{GRADING_FOLDER}/{str(student)}/")
        shutil.copy(f"{case.name}_hist.txt", f"{GRADING_FOLDER}/{str(student)}/")
        shutil.copy(f"{case.name}_output.txt", f"{GRADING_FOLDER}/{str(student)}/")
    except Exception as e:
        print(e)
        with open(f"{case.name}_error.txt", "w") as file:
            file.write(str(e))
        if student_file != None:
            student_file.write(f"{str(e)}\n")
    later = time.time()

    

    student.grades[case.name] = TestCase_Grade(f"{case.name}", f"{case.name}_hist.txt", f"{case.name}_state.txt", later - now)

    os.remove(im_name)
    switch_dir(current_directory)


def perform_tests(student: Student):
    for case in testcases:
        if testcases[case].name not in student.grades.keys():
            perform_test(student, testcases[case])


def print_students():
    for stu in students:
        print(str(stu))


def print_cases():
    for case in testcases.values():
        print(str(case))


def print_success(success: bool = True):
    for stu in students:
        if stu.successful == success:
            print(str(stu))


def test_successful():
    global student_file
    for stu in students:
        if stu.successful:
            print(str(stu))
            if not os.path.exists(f"{GRADING_FOLDER}/{str(stu)}"):
                os.mkdir(f"{GRADING_FOLDER}/{str(stu)}")
            student_file = open(f"{GRADING_FOLDER}/{str(stu)}/grader_output.txt", "w")
            history.hist_student_file = student_file
            tree.tree_student_file = student_file
            perform_tests(stu)
            stu.save_as_csv(f"{GRADING_FOLDER}/{str(stu)}")
            print("")
            student_file.close()


def retest():
    for stu in students:
        if not stu.successful:
            stu.perform_init()

    for stu in students:
        if stu.successful:
            perform_tests(stu)
            stu.save_as_csv(GRADING_FOLDER)

def create_tar():
    current_dir = os.getcwd()
    os.chdir(SUBMISSION_FOLDER)

    process = subprocess.run(f"tar -czf {STUDENT_TAR_NAME} *", shell=True, capture_output=True)
    if (process.returncode != 0):
        os.remove(STUDENT_TAR_NAME)
        print("Please put your files into Submission folder... You have 30 seconds.")
        time.sleep(30)

        process_retry = subprocess.run(f"tar -czf {STUDENT_TAR_NAME} *", shell=True, capture_output=True)

        if process_retry.returncode != 0:
            print(f"Failed to create tar file from {SUBMISSION_FOLDER}")
            print(f"Error: {process.stderr.decode()}")

    os.chdir(current_dir)

def print_grade():
    file_path = os.path.join(GRADING_FOLDER, "You 334 True", "You_334.csv");

    with open(file_path, 'r') as file:
        lines = file.readlines()

    last_line = lines[-1].strip()

    if not last_line:
        last_line = lines[-2].strip()

    grade_string = last_line.split(',')[-1].strip('"')
    grade = float(grade_string)
    print(f"Your grade is {grade}")


def init_all():
    init_testcases()
    init_students()
    print_cases()
    print_students()
    test_successful()

if __name__ == "__main__":
    os.makedirs(SUBMISSION_FOLDER, exist_ok=True)
    create_tar()

    os.makedirs(GRADING_FOLDER, exist_ok=True)

    student_path = os.path.join(STUDENT_FOLDER, "You_334")
    os.makedirs(student_path, exist_ok=True)

    tar_path = os.path.join(SUBMISSION_FOLDER, STUDENT_TAR_NAME)
    shutil.copy(tar_path, student_path)

    init_all()

    print_grade();
