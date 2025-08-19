"""
SUMO environment wrapper for RL agent using TraCI.
"""
import os
import traci
import sumolib
import numpy as np

class SumoEnv:
    def __init__(self, sumo_cfg, max_steps=1000):
        self.sumo_cfg = sumo_cfg
        self.max_steps = max_steps
        self.step = 0
        self.sumo_process = None

    def reset(self):
        if self.sumo_process:
            traci.close()
        sumo_cmd = ["sumo", "-c", self.sumo_cfg, "--no-step-log", "true"]
        traci.start(sumo_cmd)
        self.step = 0
        return self._get_state()

    def step_env(self, action):
        # Apply action (e.g., set traffic light phase)
        self._apply_action(action)
        traci.simulationStep()
        self.step += 1
        state = self._get_state()
        reward = self._get_reward()
        done = self.step >= self.max_steps
        return state, reward, done, {}

    def _apply_action(self, action):
        # Example: set phase for all traffic lights
        tls_ids = traci.trafficlight.getIDList()
        for i, tls_id in enumerate(tls_ids):
            phase = action[i] if i < len(action) else 0
            traci.trafficlight.setPhase(tls_id, phase)

    def _get_state(self):
        # Example: queue lengths at each intersection
        tls_ids = traci.trafficlight.getIDList()
        state = [traci.trafficlight.getRedYellowGreenState(tls_id) for tls_id in tls_ids]
        return np.array(state)

    def _get_reward(self):
        # Example: negative average delay
        veh_ids = traci.vehicle.getIDList()
        delays = [traci.vehicle.getAccumulatedWaitingTime(vid) for vid in veh_ids]
        if delays:
            return -np.mean(delays)
        return 0

    def close(self):
        traci.close()
