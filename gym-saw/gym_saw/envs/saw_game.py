
from __future__ import division
import gym
from gym import error, spaces, utils, core

import numpy as np
import sys

rnum = np.random.randint

class SAWGameEnv(core.Env):
    def __init__(self, L):
        self.L = L
        self.N = self.L ** 2

        self.canvas = - np.ones((self.L, self.L), dtype=np.float32)
        self.site_counter = np.zeros((self.L, self.L), dtype=np.int32)

        self.traj_sites = []
        self.traj_actions = []

        self.agent_site = (0, 0)

        ## enlarge action space to 7 operations
        self.name_mapping = dict({
                                  0 :   'right',
                                  1 :   'down',
                                  2 :   'left',
                                  3 :   'up',
                                  4 :   'lower_next',
                                  5 :   'upper_next',
                                  6 :   'noop',
                                  })

        self.index_mapping = dict({
                                  'right': 0,
                                  'down' : 1,
                                  'left' : 2,
                                  'up' : 3,
                                  'lower_next' : 4,
                                  'upper_next' : 5,
                                  'noop' : 6,
                                  })

        ### action space and state space
        self.action_space = spaces.Discrete(len(self.name_mapping))
        self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(self.L, self.L, 1))

        self.reward_range = (-1, 1)
        self.stepwise_reward = +0.01
        self.failure_penalty = -1.0
        self.step_counter = 0
        self.max_depth = 0

        self.ofilename = 'walking.log'

    def start(self, init_site=None):
        if (init_site == None):
            init_site = (rnum(self.L), rnum(self.L))
        self.start_agent(init_site)

    def start_agent(self, init_site):
        self.agent_site = init_site
        self._flip_agent_site()
        self.site_counter[self.agent_site] += 1

    def reset(self):
        self.canvas = -np.ones((self.L, self.L), dtype=np.float32)
        self.site_counter = np.zeros((self.L, self.L), dtype=np.int32)
        self.traj_actions = []
        self.traj_sites = []
        self.step_counter = 0
        # start from origin
        self.start_agent((rnum(self.L), rnum(self.L)))

        return self.get_obs()

    def complete_check(self):
        done = False
        coverage_ration = 0.6
        if (np.sum(self.canvas) >= coverage_ration * self.N):
            done = True
        return done

    def step(self, action):
        terminate = False
        intersect = False
        reward = self.stepwise_reward
        rets = []

        if (0<= action < 6):
            intersect = self.walk(action)
        elif (action == 6):
            reward = self.failure_penalty + self.stepwise_reward
            terminate = True
            '''
                In order to mimic icegame, we expect action 6 working like a 'stop' button.
                When 'stop' is called, episode terminate and avoid suffering from colliding damage.
            '''

        if (intersect):
            terminate = True
            reward = self.failure_penalty
            if (self.max_depth < self.step_counter):
                self.max_depth = self.step_counter
                print ('Penetration depth = {}'.format(self.step_counter))
                ## TODO: Write to Json
                print (self.traj_sites)
                with open(self.ofilename, 'a') as f:
                    f.write('{}\n'.format(self.traj_sites))
                self.render()

        if(self.complete_check()):
            reward = +1.0
            terminate = True
            print ('Complete SAW! with {} steps.'.format(self.step_counter))
            self.render()

        obs = self.get_obs()
        return obs, reward, terminate, rets

    def walk(self, dir):
        collide = False
        x, y = self.agent_site
        xp = x + 1 if x < self.L-1 else x
        xm = x - 1 if x > 0        else x
        yp = y + 1 if y < self.L-1 else y
        ym = y - 1 if y > 0        else y

        if (type(dir) == str):
            dir = self.index_mapping[dir]

        if (dir == 0):
            self.agent_site = (x, ym)
        elif (dir == 1):
            self.agent_site = (x, yp)
        elif (dir == 2):
            self.agent_site = (xp, y)
        elif (dir == 3):
            self.agent_site = (xm, y)
        elif (dir == 4):
            if((x+y) % 2 == 0):
                self.agent_site = (xp, yp)
            else:
                self.agent_site = (xm, yp)
        elif (dir == 5):
            if((x+y) % 2 == 0):
                self.agent_site = (xm, ym)
            else:
                self.agent_site = (xp, ym)

        self.traj_sites.append(self.agent_site)
        self.traj_actions.append(dir)
        self.step_counter += 1

        collide = self._flip_agent_site()
        return collide

    def _flip_agent_site(self):
        visited = False
        if (self.site_counter[self.agent_site] >= 1):
            visited = True
        self.canvas[self.agent_site] *= -1
        self.site_counter[self.agent_site] += 1
        return visited

    def _pdb(self, s, d, l):
        return ((s+d) % l + l ) % l

    def timeout(self):
        return False

    def render(self, mode='ansi', close=False):
        screen = '\r'
        screen += '\n\t'
        screen += '+' + self.L * '---' + '+\n'
        for i in range(self.L):
            screen += '\t|'
            for j in range(self.L):
                p = (i, j)
                spin = self.canvas[p]
                if spin == -1:
                    screen += '   '
                elif spin == +1:
                    screen += ' o '
            screen += '|\n'
        screen += '\t+' + self.L * '---' + '+\n'
        sys.stdout.write(screen)

    # stack 4 copy of canvas
    def get_obs(self):
        x_t = self.canvas.reshape(self.L, self.L)
        return np.stack((x_t, x_t, x_t, x_t), axis = 2)

    @property
    def unwrapped(self):
        """Completely unwrap this env.
            Returns:
                gym.Env: The base non-wrapped gym.Env instance
        """
        return self
