"""
RL training loop for SUMO traffic signal control.
"""
from sumo_env import SumoEnv
from rl_agent import RLAgent

SUMO_CFG = "sumo_rl/networks/4_intersections.sumocfg"
MAX_EPISODES = 10
MAX_STEPS = 1000

if __name__ == "__main__":
    env = SumoEnv(SUMO_CFG, max_steps=MAX_STEPS)
    agent = RLAgent(n_actions=4, state_dim=4)  # 4 intersections

    for episode in range(MAX_EPISODES):
        state = env.reset()
        total_reward = 0
        for t in range(MAX_STEPS):
            action = agent.select_action(state)
            next_state, reward, done, _ = env.step_env(action)
            agent.update(state, action, reward, next_state)
            state = next_state
            total_reward += reward
            if done:
                break
        print(f"Episode {episode+1}: Total Reward = {total_reward:.2f}")
    env.close()
