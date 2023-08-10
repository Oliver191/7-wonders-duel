import os
from multiprocessing import Pool

# alpha = [0.05]
# epsilon = [0.02]
# gamma = [0.5, 0.55, 0.65, 0.7]
# maxAttempts = [2]
#
# # define the command to run the script with argument
# cmd = 'python seven_wonders_duel.py -t 200000 -g 210000 -a1 RuleBasedAgent -a2 LearningAgent -s True'
# # ~10 min pro 20k with 8 threads
#
# def run_cmd(alpha, epsilon, gamma, maxAttempts):
#     current_cmd = cmd + ' -alp ' + str(alpha) + ' -eps ' + str(epsilon) + ' -gam ' + str(gamma) + ' -mA ' + str(maxAttempts)
#     current_cmd += ' -s2 RL_Q_200k_' + str(alpha) + '_' + str(epsilon) + '_' + str(gamma) + '_' + str(maxAttempts)
#     os.system(current_cmd)
#
# if __name__ == "__main__":
#     with Pool(processes=8) as pool: # Set the number of processes to use
#         results = [pool.apply_async(run_cmd, (a, e, g, m)) for a in alpha for e in epsilon for g in gamma for m in maxAttempts]
#         output = [p.get() for p in results]


agents1 = ['RandomAgent', 'RuleBasedAgent', 'GreedyCivilianAgent', 'GreedyMilitaryAgent', 'GreedyScientificAgent']
agents1 = ['a']
agents2 = ['1', '2', '3', '4', '5', '6', '7', '8']
cmd = 'python seven_wonders_duel.py -t 100000 -g 110000 -a1 RuleBasedAgent'
cmd2 = ' -a2 LearningAgent -s True -alp 0.05 -eps 0.02 -gam 0.5 -mA 2'
def run_cmd(agents1, agents2):
    current_cmd = cmd + cmd2 + ' -l2 RL_Q_200k_0.05_0.02_0.65_2 ' + '-s2 RL_Q_200k_0.05_0.02_0.65_2_try' + str(agents2)
    os.system(current_cmd)

if __name__ == "__main__":
    with Pool(processes=8) as pool: # Set the number of processes to use
        results = [pool.apply_async(run_cmd, (a1, a2)) for a1 in agents1 for a2 in agents2]
        output = [p.get() for p in results]
