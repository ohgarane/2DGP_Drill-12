from pico2d import *

import random
import math
import game_framework
import game_world
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector
import play_mode

# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images is None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image(f"./zombie/{name} ({i}).png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)

    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0  # 방향(라디안)
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0  # 좀비가 가지고 있는 공 개수

        self.build_behavior_tree()
        self.patrol_locations = [(43, 274), (1118, 274), (1050, 494), (575, 804), (235, 991), (575, 804), (1050, 494),
                                 (1118, 274)]
        self.loc_no = 0

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50

    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        self.bt.run()

    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        draw_rectangle(*self.get_bb())

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1

    def set_random_location(self):
        self.tx, self.ty = random.randint(100, 1280 - 100), random.randint(100, 1024 - 100)
        return BehaviorTree.SUCCESS

    def move_slightly_to(self, tx, ty):
        self.dir = math.atan2(ty - self.y, tx - self.x)
        distance = RUN_SPEED_PPS * game_framework.frame_time
        self.x += distance * math.cos(self.dir)
        self.y += distance * math.sin(self.dir)

    def move_to_target(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(self.tx, self.ty)
        if self.distance_less_than(self.tx, self.ty, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def is_boy_nearby(self, r=7.0):
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def compare_ball_count(self):
        # 공 개수 비교
        if self.ball_count >= play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS  # 추적
        else:
            return BehaviorTree.FAIL  # 도망

    def chase_boy(self):
        self.state = 'Walk'
        self.move_slightly_to(play_mode.boy.x, play_mode.boy.y)
        return BehaviorTree.RUNNING

    def flee_from_boy(self):
        self.state = 'Walk'
        # 소년 반대 방향으로 이동
        dx, dy = self.x - play_mode.boy.x, self.y - play_mode.boy.y
        flee_distance = RUN_SPEED_PPS * game_framework.frame_time
        norm = math.sqrt(dx ** 2 + dy ** 2)
        self.x += flee_distance * (dx / norm)
        self.y += flee_distance * (dy / norm)
        return BehaviorTree.RUNNING

    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2

    def build_behavior_tree(self):
        # 배회 행동
        wander_action = Action('Set random location', self.set_random_location)
        wander_move = Action('Move to target', self.move_to_target)
        wander = Sequence('Wander', wander_action, wander_move)

        # 소년이 근처에 있는지 확인
        boy_nearby = Condition('Is boy nearby?', self.is_boy_nearby)

        # 공 개수 비교 후 행동 결정
        compare_balls = Condition('Compare ball count', self.compare_ball_count)
        chase_boy = Action('Chase boy', self.chase_boy)
        flee_boy = Action('Flee from boy', self.flee_from_boy)
        chase_or_flee = Selector('Chase or Flee', Sequence('Chase', compare_balls, chase_boy), flee_boy)

        # 최종 행동 트리
        root = Selector('Zombie Behavior', Sequence('React to Boy', boy_nearby, chase_or_flee), wander)
        self.bt = BehaviorTree(root)
