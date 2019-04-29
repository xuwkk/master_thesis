# -*- coding: utf-8 -*-

"""

"""
import os

__author__ = 'Vegard Solberg'
__email__ = 'vegard.ulriksen.solberg@nmbu.no'

from gym_power.envs import PowerEnv, PowerEnvSparse
from gym_power.envs.power_env import PowerEnvOld
from gym_power.envs.active_network_env import ActiveEnv
from stable_baselines.common.vec_env.dummy_vec_env import DummyVecEnv
from stable_baselines.common.vec_env import VecNormalize
from stable_baselines.ddpg.policies import MlpPolicy, LnMlpPolicy
from stable_baselines.ddpg.noise import OrnsteinUhlenbeckActionNoise
from stable_baselines import DDPG
from stable_baselines.ddpg.noise import AdaptiveParamNoiseSpec
import pickle
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import tensorflow as tf

powerenv = ActiveEnv()
powerenv.set_parameters({'state_space': ['sun','demand'],
                         'reward_terms':['voltage','current']})

powerenv = DummyVecEnv([lambda: powerenv])
action_mean = np.zeros(powerenv.action_space.shape)
action_sigma = 0.3 * np.ones(powerenv.action_space.shape)
action_noise = OrnsteinUhlenbeckActionNoise(mean=action_mean,
                                            sigma=action_sigma)

param_noise = AdaptiveParamNoiseSpec(initial_stddev=0.2,
                                     desired_action_stddev=0.01)

t_steps = 800000
logdir = 'C:\\Users\\vegar\\Dropbox\\Master\\logs'
powermodel = DDPG(LnMlpPolicy, powerenv,
                  verbose=2,
                  action_noise=action_noise,
                  gamma=0.99,
                  #param_noise=param_noise,
                  tensorboard_log=logdir,
                  memory_limit=int(80000),
                  nb_train_steps=50,
                  nb_rollout_steps=100,
                  critic_lr=0.001, #default: 0.001
                  actor_lr=0.0001, #default: 0.0001
                  normalize_observations=False)
powermodel.learn(t_steps)

env = powerenv.envs[0]
net = env.powergrid
sol_bus = net.load['bus'].isin(net.sgen['bus'])

data = []
obs = powerenv.reset()


model_name = 'overnight_reactive'
path = 'models/' + model_name +'.pkl'
while os.path.isfile(path):
    model_name += '1'
    path = 'models/' + model_name + '.pkl'
powermodel.save('models/'+model_name)
with open('models/' + model_name + '_params.p', 'wb') as f:
    pickle.dump(env.params, f)


for i in range(100):
    action,_ = powermodel.predict(obs)
    obs, rewards, dones, info = powerenv.step(action)
    line = {}
    for i,act in enumerate(action[0]):
        line[i] = act
    data.append(line)

df = pd.DataFrame(data)
df['demand'] =env.get_episode_demand_forecast()[0][:100]
df['sol'] =env.get_episode_solar_forecast()[:100]
df.loc[:,['demand','sol',3]].plot()
plt.show()



