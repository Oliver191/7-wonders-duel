import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy import stats
import numpy as np


# Mean win rate and standard deviation of results

df_random = pd.read_csv('testing_data/DRLvsRandom100x1000.csv')
df_civilian = pd.read_csv('testing_data/DRLvsCivilian100x1000.csv')
df_military = pd.read_csv('testing_data/DRLvsMilitary100x1000.csv')
df_scientific = pd.read_csv('testing_data/DRLvsScientific100x1000.csv')
df_rulebased = pd.read_csv('testing_data/DRLvsRuleBased100x1000.csv')

df_noMask = pd.read_csv('testing_data/DRLvsNoMask100x1000.csv')
df_noMaskOrTuning = pd.read_csv('testing_data/DRLvsNoMaskOrTuning100x1000.csv')
df_noTuning = pd.read_csv('testing_data/DRLvsNoTuning100x1000.csv')

pd.set_option('display.max_columns', None)

print(df_noTuning.describe().loc[['mean', 'std']].round(decimals = 4))



# T-test

# mu = 834.23
# sigma = 12.6562
# n = 100
# mu0 = 500
#
# t = (mu - mu0) / (sigma / np.sqrt(n))
# df = n - 1
# p = 1 - stats.t.cdf(t, df=df)
#
# print(f"t statistic: {t}")
# print(f"p value: {p}")


# Training graphs

# df_value = pd.read_csv('training_graphs/valueLoss_PPO_final_all.csv')
# df_policy = pd.read_csv('training_graphs/policyLoss_PPO_final_all.csv')
# df_entropy = pd.read_csv('training_graphs/entropyLoss_PPO_final_all.csv')
# df_variance = pd.read_csv('training_graphs/variance_PPO_final_all.csv')
# df_clip = pd.read_csv('training_graphs/clipFraction_PPO_final_all.csv')
# df_kl = pd.read_csv('training_graphs/kl_PPO_final_all.csv')
#
#
# def format_xaxis(x, pos):
#     return '%1.0fk' % (x * 1e-3)
#
# fig, axs = plt.subplots(3, 2, figsize=(15,15)) # 1 row, 2 columns, figure size is 15x5 inches
#
# dataframes = [df_value, df_policy, df_entropy, df_variance, df_clip, df_kl]
# names = ['Value Loss', 'Policy Gradient Loss', 'Entropy Loss', 'Explained Variance', 'Clip Fraction', 'Kullback-Leibler Divergence']
# ids = ['(a) ', '(b) ', '(c) ', '(d) ', '(e) ', '(f) ']
#
# for i, df in enumerate(dataframes):
#     row = i // 2
#     col = i % 2
#     axs[row, col].plot(df['Step'], df['Value'], label='Final DRL Agent', color='C1')
#     axs[row, col].set_title(ids[i] + names[i] + ' per Time-Step')
#     axs[row, col].set_xlabel('Time-Steps')
#     axs[row, col].set_ylabel(names[i])
#     axs[row, col].legend()
#     formatter = FuncFormatter(format_xaxis)
#     axs[row, col].xaxis.set_major_formatter(formatter)
#
# plt.tight_layout()
#
# fig.savefig('training_graphs/finalTrainingMetrics.png', dpi=300, bbox_inches='tight')
# plt.show()






# df_tuning_value = pd.read_csv('training_graphs/valueLoss_PPO_final_all.csv')
# df_noTuning_value = pd.read_csv('training_graphs/valueLoss_train_noTuning_1.5M_0.csv')
# #
# df_tuning_policy = pd.read_csv('training_graphs/policyLoss_PPO_final_all.csv')
# df_noTuning_policy = pd.read_csv('training_graphs/policyLoss_train_noTuning_1.5M_0.csv')
#
# def format_xaxis(x, pos):
#     return '%1.0fk' % (x * 1e-3)
#
# fig, axs = plt.subplots(1, 2, figsize=(15,5)) # 1 row, 2 columns, figure size is 15x5 inches
#
# # First subplot
# axs[0].plot(df_noTuning_value['Step'], df_noTuning_value['Value'], label='DRL Agent without Tuning')
# axs[0].plot(df_tuning_value['Step'], df_tuning_value['Value'], label='DRL Agent with Tuning')
# axs[0].set_title('(a) Value Loss per Time-Step')
# axs[0].set_xlabel('Time-Steps')
# axs[0].set_ylabel('Value Loss')
# axs[0].set_ylim(bottom=0)
# axs[0].legend()
# formatter = FuncFormatter(format_xaxis)
# axs[0].xaxis.set_major_formatter(formatter)
#
# # Second subplot
# axs[1].plot(df_noTuning_policy['Step'], df_noTuning_policy['Value'], label='DRL Agent without Tuning')
# axs[1].plot(df_tuning_policy['Step'], df_tuning_policy['Value'], label='DRL Agent with Tuning')
# axs[1].set_title('(b) Policy Gradient Loss per Time-Step')
# axs[1].set_xlabel('Time-Steps')
# axs[1].set_ylabel('Policy Gradient Loss')
# axs[1].legend()
# formatter = FuncFormatter(format_xaxis)
# axs[1].xaxis.set_major_formatter(formatter)
#
# plt.tight_layout()
#
# fig.savefig('training_graphs/noTuning_ValuePolicyLoss.png', dpi=300, bbox_inches='tight')
# plt.show()
