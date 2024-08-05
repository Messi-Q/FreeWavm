import random
import bisect
import math


# Roulette Wheel Selection
def weighted_choice(choices):
    total_weight = sum(weight for element, weight in choices)
    rand_value = random.uniform(0, total_weight)

    current_weight = 0
    for element, weight in choices:
        current_weight += weight
        if current_weight >= rand_value:
            return element
        

# Roulette Wheel Selection Optimized Version
class weighted_random_choice(object):
    def __init__(self, weights):
        self.elements, self.weights = zip(*weights)
        self.cumulative_weights = self.compute_cumulative_weights()

    def compute_cumulative_weights(self):
        total = 0
        cumulative_weights = []
        for weight in self.weights:
            total += weight
            cumulative_weights.append(total)
        return cumulative_weights
    
    def weighted_choice(self):
        rand_value = random.uniform(0, self.cumulative_weights[-1])
        index = bisect.bisect_right(self.cumulative_weights, rand_value)
        return self.elements[index]


# Thompson Sampling 
class ThompsonSampling:
    def __init__(self, num_arms):
        self.num_arms = num_arms
        self.alpha = [1] * num_arms
        self.beta = [1] * num_arms
    
    def choose_arm(self):
        theta_samples = [random.betavariate(self.alpha[i], self.beta[i]) for i in range(self.num_arms)]
        chosen_arm = max(range(self.num_arms), key=lambda i: theta_samples[i])
        return chosen_arm
    
    def update_parameters(self, chosen_arm, reward):
        if reward == 1:
            self.alpha[chosen_arm] += 1
        else:
            self.beta[chosen_arm] += 1


# Adapative Thompson Sampling 
class AdapativeThompsonSampling:
    def __init__(self, num_arms):
        self.num_arms = num_arms
        self.alpha = [1] * num_arms  # Alpha
        self.beta = [1] * num_arms  # Beta 
        self.t = 0  # total time step
    
    def choose_arm(self):
        theta_samples = [random.betavariate(self.alpha[i], self.beta[i]) for i in range(self.num_arms)]
        chosen_arm = max(range(self.num_arms), key=lambda i: theta_samples[i])
        return chosen_arm
    
    def update_parameters(self, chosen_arm, reward):
        self.t += 1
        self.alpha[chosen_arm] += reward
        self.beta[chosen_arm] += 1 - reward

 
# Epsilon-Greedy Algorithm
class EpsilonGreedy:
    def __init__(self, num_arms, epsilon):
        self.num_arms = num_arms
        self.epsilon = epsilon
        self.q_values = [0] * num_arms
        self.arm_pulls = [0] * num_arms
    
    def choose_arm(self):
        if random.random() < self.epsilon:
            chosen_arm = random.choice(range(self.num_arms))
        else:
            chosen_arm = max(range(self.num_arms), key=lambda i: self.q_values[i])
        return chosen_arm
    
    def update_parameters(self, chosen_arm, reward):
        self.arm_pulls[chosen_arm] += 1
        current_q = self.q_values[chosen_arm]
        self.q_values[chosen_arm] = (current_q * (self.arm_pulls[chosen_arm] - 1) + reward) / self.arm_pulls[chosen_arm]


# Adapative Epsilon-Greedy Algorithm
class AdapativeEpsilonGreedy:
    def __init__(self, num_arms, initial_epsilon):
        self.num_arms = num_arms
        self.epsilon = initial_epsilon
        self.q_values = [0] * num_arms
        self.arm_pulls = [0] * num_arms
        self.t = 0
    
    def choose_arm(self):
        if random.random() < self.epsilon:
            chosen_arm = random.choice(range(self.num_arms))
        else:
            chosen_arm = max(range(self.num_arms), key=lambda i: self.q_values[i])
        return chosen_arm
    
    def update_parameters(self, chosen_arm, reward):
        self.t += 1
        self.arm_pulls[chosen_arm] += 1
        current_q = self.q_values[chosen_arm]
        self.q_values[chosen_arm] = (current_q * (self.arm_pulls[chosen_arm] - 1) + reward) / self.arm_pulls[chosen_arm]
        # adjust epsilon adaptively, such as 1 / t
        self.epsilon = 1 / math.sqrt(self.t)
        

# unit test
if __name__ == "__main__":
    num_arms = 5
    epsilon = 0.1
    epsilon_greedy = AdapativeEpsilonGreedy(num_arms, epsilon)
    # thompson_sampler = AdapativeThompsonSampling(num_arms)
    
    num_rounds = 1000
    for _ in range(num_rounds):
        chosen_arm = epsilon_greedy.choose_arm()
        reward = random.choice([0, 1])
        epsilon_greedy.update_parameters(chosen_arm, reward)
