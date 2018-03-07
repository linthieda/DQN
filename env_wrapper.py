#!/usr/bin/env python
from collections import deque
import numpy as np
import gym, sys, copy, argparse
from utils import image_prep
from gym import wrappers

class EnvWrapper(object):
    def __init__(self, args, mod_r=False):
        self.env_name = args.env
        if args.use_monitor:
            self.env = wrappers.Monitor(gym.make(self.env_name), 'tmp/{}_{}_record'.format(args.env, args.qnum), force=True)
        else:
            self.env = gym.make(self.env_name)
        self.num_actions = self.env.action_space.n
        self.state_shape = self.env.observation_space.shape
        self.frame_stack = None
        self.si = None
        self.prep = None

        # register methods
        self.reset = self.env.reset
        self.render = self.env.render
        self.step = self.env.step

        if self.env_name == 'SpaceInvaders-v0':
            self.state_shape = (4, 84, 84)
            self.frame_stack = 4
            self.si = deque(iterable=[], maxlen=self.frame_stack)
            self.step = self.step_frame
            self.reset = self.reset_frame
            self.prep = image_prep

        if self.env_name == 'MountainCar-v0' and mod_r:
            self.reset = self.reset_mountain_car
            self.step = self.step_mountain_car
        return

    def step_frame(self, a):
        si, r, done, info = self.env.step(a)
        self.si.append(self.prep(si))
        s = np.array(self.si)
        return s, r, done, info

    def reset_frame(self):
        self.si.append(self.prep(self.env.reset()))
        for i in range(1, self.frame_stack):
            si, _, _, _ = self.env.step(np.random.randint(self.num_actions))
            self.si.append(self.prep(si))
        s = np.array(self.si)
        return s

    def step_mountain_car(self, a):
        si, r, done, info = self.env.step(a)

        h = np.sin(3 * si[0]) * 0.45 + 0.55

        v_update = np.cos(3 * self.si[0]) * (-0.0025)

        r_update = (si[1] - self.si[1] - v_update) * np.sign(si[1]) * 2000.0

        if abs(si[1]) >= 0.07:
            r_update = 0.8

        if h > 0.55:
            r += r_update * 1.1

        else:
            r += r_update

        self.si = si
        return si, r, done, info

    def reset_mountain_car(self):
        self.si = self.env.reset()
        return self.si