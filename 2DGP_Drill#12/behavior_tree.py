import game_framework
import math

level = 0
def indent():
    global level
    level += 1

def unindent():
    global level
    level -= 1

def print_indent():
    for i in range(level):
        print("    ", end='')

def build_behavior_tree(self):
    a1 = Action('Set target location', self.set_target_location, 1000, 1000)
    a2 = Action('Move to', self.move_to)
    root = move_to_target_location = Sequence('Move to target location', a1, a2)
    self.bt = BehaviorTree(root)

def update(self):
 self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
 self.bt.run()

class BehaviorTree:
    FAIL, RUNNING, SUCCESS = -1, 0, 1
    FAIL, RUNNING, SUCCESS, UNDEF = 'FAIL', 'RUNNING', 'SUCCESS', 'UNDEF'

    # how to run node?
    # 'EVAL' : evaluate all nodes
    # 'MONITOR' : evaluate only condition nodes
    run_mode = 'EVAL'

    def __init__(self, root_node):
        self.root = root_node
        self.root.tag_condition()

    def run(self):
        print('\n========================================== NEW TICK =======================================================')
        self.root.run()
        if self.root.value == BehaviorTree.SUCCESS:
            self.root.reset()


class Node:

    def add_child(self, child):
        self.children.append(child)
    def add_children(self, *children):
        for child in children:
            self.children.append(child)
    @staticmethod
    def show_result(f):
        def inner(self):
            result = f(self)
            print(f'[{self.__class__.__name__:10s}] {self.name:40s} ==> ({result})')
            return result

        return inner


class Selector(Node):
    def __init__(self, name, *nodes):
        self.children = list(nodes)
        self.name = name
        self.value = BehaviorTree.UNDEF
        self.has_condition = False
        self.prev_running_pos = 0

    def reset(self):
        self.value = BehaviorTree.UNDEF
        for child in self.children:
            child.reset()

    def tag_condition(self):
        for child in self.children:
            child.tag_condition()
            if child.has_condition:
                self.has_condition = True


    def reset(self):
        self.prev_running_pos = 0
        for node in self.children:
            node.reset()


    @Node.show_result
    def run(self):
        for i, child in enumerate(self.children):
            print(i, child.value, child.has_condition)
            if (child.value in (BehaviorTree.UNDEF, BehaviorTree.RUNNING)) or child.has_condition:
                self.value = child.run()
                if self.value in (BehaviorTree.RUNNING, BehaviorTree.SUCCESS):
                    return self.value

        self.value = BehaviorTree.FAIL
        return self.value

class Sequence(Node):
    def __init__(self, name, *nodes):
        self.children = list(nodes)
        self.name = name
        self.value = BehaviorTree.UNDEF
        self.has_condition = False
        self.prev_running_pos = 0

    def reset(self):
        self.value = BehaviorTree.UNDEF
        for child in self.children:
            child.reset()

    def tag_condition(self):
        for child in self.children:
            child.tag_condition()
            if child.has_condition:
                self.has_condition = True



    @Node.show_result
    def run(self):
        for child in self.children:
            if (child.value in (BehaviorTree.UNDEF, BehaviorTree.RUNNING)) or child.has_condition:
                self.value = child.run()
                if self.value in (BehaviorTree.RUNNING, BehaviorTree.FAIL):
                    return self.value

        self.value = BehaviorTree.SUCCESS
        return self.value



class Action(Node):
    def __init__(self, name, func, *args):
        self.name = name
        self.func = func
        self.args = list(args) if args else []
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def tag_condition(self):
        self.has_condition = False

    def reset(self):
        self.value = BehaviorTree.UNDEF
        pass

    def add_child(self, child):
        print("ERROR: you cannot add child node to leaf node")

    def add_children(self, *children):
        print("ERROR: you cannot add children node to leaf node")

    @Node.show_result
    def run(self):
        self.value = self.func(*self.args)
        return self.value
    def move_to(self, r = 0.5):
        self.state = 'Walk'
        self.move_slightly_to(self.tx, self.ty)
        if self.distance_less_than(self.tx, self.ty, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def set_target_location(self, x=None, y=None):
        if not x or not y:
            raise ValueError('Location should be given')
        self.tx, self.ty = x, y
        return BehaviorTree.SUCCESS

    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2

    def move_slightly_to(self, tx, ty):
        self.dir = math.atan2(ty - self.y, tx - self.x)
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)

    # @Node.show_result
    # def monitor_run(self):
    #     return self.result, 'no change' # monitor run 시에는 기존 실행 결과를 재활용.


class Condition(Node):
    def __init__(self, name, func, *args):
        self.name = name
        self.func = func
        self.args = list(args) if args else []
        self.value = BehaviorTree.UNDEF
        self.has_condition = False

    def reset(self):
        self.value = BehaviorTree.UNDEF

    def tag_condition(self):
        self.has_condition = True

    def add_child(self, child):
        print("ERROR: you cannot add child node to leaf node")

    def add_children(self, *children):
        print("ERROR: you cannot add children node to leaf node")

    @Node.show_result
    def run(self):
        self.value = self.func(*self.args)
        if self.value == BehaviorTree.RUNNING:
            print("ERROR: condition node cannot return RUNNING")
            raise ValueError;

        return self.value
