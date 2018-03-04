#!/usr/bin/env python

import tensorflow as tf
import numpy as np
import gym, sys, copy, argparse

from memory_replay import MemoryReplayer
from deep_qn import DeepQN
from tester import Tester
from plotter import Plotter



def main():
    print(tf.__version__)
    gpu_ops = tf.GPUOptions(allow_growth=True)
    config = tf.ConfigProto(gpu_options=gpu_ops)
    sess = tf.Session(config=config)

    env = gym.make('CartPole-v0')
    mr = MemoryReplayer(env, cache_size=100000)

    # set type='v1' for linear model, 'v3' for three layer model (two tanh activations)

    qn = DeepQN(state_shape=mr.state_shape, num_actions=mr.num_actions, gamma=0.99, type='v1')

    qn.reset_sess(sess)

    qn.set_train(0.001)

    init = tf.global_variables_initializer()
    sess.run(init)

    plotter = Plotter()

    testor = Tester(qn, env, report_interval=100)

    print('Pretrain test:')
    testor.run(qn, sess)

    score = []

    for epi in range(1000000):
        s = env.reset()

        done = False

        rc = 0

        while not done:
            a = qn.select_action_eps_greedy(get_eps(epi), s)

            a_ = a[0]

            s_, r, done, _ = env.step(a_)

            mr.remember(s, s_, r, a_, done)

            s = s_

            rc += r

        score.append(rc)

        # replay

        s, s_, r, a, done = mr.replay(batch_size=64)

        qn.train(s, s_, r, a, done)

        if (epi + 1) % 200 == 0:
            avg_score = np.mean(score)
            plotter.plot(avg_score)
            print('avg score last 200 episodes ', avg_score)
            score = []
            if avg_score > 195:
                break

    return


def get_eps(t):
    return max(0.01, 1.0 - np.log10(t + 1) * 0.995)

if __name__ == '__main__':
    main()