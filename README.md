# 7-Wonders-Duel

The GitHub repository accompanying the MSc Thesis at KCL written by Oliver Caspers regarding the topic “AI for non-deterministic Board Games: Developing an AI Agent using Deep Reinforcement Learning for the Game 7 Wonders Duel”. Submitted on the 15.08.2023.

### originalityStatement.txt: 
Text file which includes the statement certifying the work as my own unless otherwise specified. Note that the project was built upon the unfinished version of 7 Wonders Duel, forked from Github (https://github.com/ygoduelistharry/7-wonders-duel) on the 20.02.2023. This was also credited in the project report with a description of the game state at the time it was forked as well as a list of all the features added, and changes made. The code of the initial game can still be found at: old_custom_environment/forked_seven_wonders_duel.py with the old adjusted environment at: old_custom_environment/seven_wonders_duel.py and the new redesigned game environment at: WondersDuelEnv.py. All changes made and code added can also directly be traced on GitHub (https://github.com/ygoduelistharry/7-wonders-duel/compare/master...Oliver191:7-wonders-duel:master).

### initialGameLog.docx: 
Word file which keeps track of the initial game state at the time it was forked, changes made, and features added.

### WondersDuelEnv.py:
Python file which contains the board game 7 Wonders Duel. Was built upon the custom environment of the gymnasium library. Can take an agent as input during initialization to specify an opponent to play against. Main functions include *step()* (to take an action within the environment), *reset()* (to set or reset the game environment to start a new game), and *render()* (to visualize the game state). Can be used in conjunction with e.g. *playEnv.py* to play the game.

### WondersVisual.py:
Python file which is used by *WondersDuelEnv.py* to display the game environment using the pygame library. Displays, for example, the wonder available for selection during wonder drafting or the age board during the main game loop. Within the main game loop, the “W” and “S” keys can be used to switch between the military board, the age board, and the player boards. Pressing any other key closes the display. 

### playEnv.py:
Python file which can be used by a human to play a game against one of the agents. The agent can be specified through the *player2* variable in string form. The agent needs to be within the folder baselines3_agents and be created with the Stable Baselines3 library. The user can play through the command line. The action “s” displays the game, “q” quits the game, or otherwise needs to be a valid move. “c” plus the number of the respective card constructs the card in the player board, while “d” plus the card number discards it for coins. “w” plus card number and wonder number, uses a card from the board to construct the specified wonder. 

### baselineAgents.py:
Python file containing all the five baseline agents i.e. *RandomAgent*, *GreedyCivilianAgent*, *GreedyMilitaryAgent*, *GreedyScientificAgent*, and *RuleBasedAgent*. These are usually used within the environment to train or test a DRL agent. After initialization they can be used through the *getAction()* function to predict an action. 

### WondersTest.py:
Python file which can be used to test two agents against one another over multiple games. The agents can be specified through the *player1* and *player2* variables in string form. Baseline agents from *baselineAgents.py* or DRL agents from the folder baselines3_agents can be used. The variable *games* can be used to specify the number of games played. Setting *show* to True displays games in the command line, while setting *show* to False suppresses the print statements. Also contains code which can be used to save the results in a .csv file. 

### wondersLearn.py:
Python file which can be used to create or fine-tune DRL agents. The variable *n_steps* specifies the number of training time-steps while the *games* variable specifies the training repetitions. The variable *player1* can be used to specify the baseline or DRL opponent and *agent2* specifies the PPO to train. The trained agent is saved in the folder baselines3_agents, named according to the *name* variable, with the tensorboard training logs saved to the tensorboard_logs folder.

### optimizeDRL.py:
Python file which relies on the optuna library to search for hyperparameters and store them in a SQL database together with an average win rate. Hyperparameter suggestions improve over time based on the win rate of the hyperparameters. Can be run in parallel by executing it multiple times. *agent1* specifies the opponent, while the hyperparameters and their ranges can be defined within the *objective()* function in the *hyperparams* dictionary. The *model* variable specifies the DRL agent to train and the *path* variable defines the name and path where the SQL database is saved. 

### trainingGraphs.py:
Python file which was used to plot the data from tensorboard to generate the figures used in the thesis. It also contains the code used for the t-test. 

### requirements.txt:
Text file which contains all the libraries used and their version.

### WondersMCTS.py:
Python file which was used to perform monte-carlo tree search (MCTS). The *human* variable can be used to set the opponent of the MCTS agent to human or agent input. With agent input the *player1* variable can be used to specify either a baseline or DRL agent. Did not end up being included in the thesis because it basically creates a copy of the current game state and plays ahead to find the best actions before returning to the starting game state. However, it shouldn’t be able to know the hidden cards available in the game ahead of time. 

### game_data:
Folder which contains the .csv files, containing necessary game information such as card names, cost, effect, type, board layout, information on wonders, etc. The files card_list.csv and age_layout.csv were also forked from the GitHub mentioned in the beginning. 

### images:
Folder containing the images with which *WondersVisual.py* display the game state. Images include e.g. pictures of cards, wonders, progress tokens, etc.

### old_custom_environment:
Folder which contains the custom game environment which was used before converting to Stable Baselines3. It contains the game at the time it was forked from GitHub i.e. *forked_seven_wonders_duel.py* and the adjusted game environment with all the features added i.e. *seven_wonders_duel.py*. *seven_wonders_duel.py* contains the finished game and provides an alternative way of playing 7 Wonders Duel. Here the file itself can be run with parameters to specify agents and players. Within the game_data folder, the files card_list.csv and age_layout.csv were also forked from the GitHub mentioned in the beginning. 

### baselines3_agents:
Folder which contains all the trained DRL agents left after the clean-up. They are of type *MaskablePPO* and the final trained DRL agent is called “PPO_final_DRL_agent_1.5M”. 

### tensorboard_logs:
Folder which contains all the tensorbaord logs left after clean-up. Can be used with tensorboard to display key metrics recorded during training. “PPO_final_DRL_agent_1.5M” contains all the logs of the final trained DRL agent. 

### SQL_databases:
Folder which contains all SQL databases which were used for hyperparameter tuning to store the hyperparameters together with their corresponding mean win rate. 

### testing_data:
Folder which contains the testing data of the final DRL agent in .csv files used in the thesis. They were generated through repeating 1,000 games 100 times against each of the baseline agents as well as DRL agents trained without masking, without tuning, and without masking nor tuning.

### training_data: 
Folder which contains the training data used in the thesis converted from tensorbaord to .csv files. The .csv files contain the key metrics recorded during training. 
