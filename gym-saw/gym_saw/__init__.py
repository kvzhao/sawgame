import logging
from gym.envs.registration import register

logger = logging.getLogger(__name__)

register (
    id = 'SAWGameEnv-v0',
    entry_point='gym_saw.envs:SAWGameEnv',
    kwargs={
        'L' : 32,
    },
    )
