LEVEL0=0######start from zero to work as list index
LEVEL1=1######
LEVEL2=2######
LEVEL4=3
NUMBER_OF_LEVELS=3
SWITCH_NODE=0
HOST_NODE=1
STATELESS=1
STATEFUL=2
EQUAl_FLOW_DISTRIBUTION=0
NOT_EQUAl_FLOW_DISTRIBUTION=1
#Algorithms
ALGORITHM_BFD=0
ALGORITHM_FFD=1
ALGORITHM_BFD_SINGLE_INSTANCE=2
ALGORITHM_BFD_COMP_PLUS_COMM=3
ALGORITHM_BFD_comm=4
ALGORITHM_BFD_STATELESS=5
ALGORITHM_BFD_STATEFUL=6
ALGORITHM_BFA_COMP=7
ALGORITHM_BF=8
ALGORITHM_FF=9
ALGORITHM_RANDOM=10
ALGORITHM_CP_COMP=11
ALGORITHM_CP_COMM=12
ALGORITHM_CP_COMP_PLUS_COMM=13
ALGORITHM_CP_STATEFUL_PERC=14
ALGORITHM_CP_STATELESS_PERC=15
ALGORITHM_TABU_BFD_MOVE=16
ALGORITHM_TABU_BFD_SINGLE_SWAP=17
ALGORITHM_TABU_BFD_DOUBLE_SWAP=18
ALGORITHM_TABU_BFD_ALL_MOVES=19
ALGORITHM_TABU_RANDOM_MOVE=20
ALGORITHM_TABU_RANDOM_SINGLE_SWAP=21
ALGORITHM_TABU_RANDOM_DOUBLE_SWAP=22
ALGORITHM_TABU_RANDOM_ALL_MOVES=23
ALGORITHM_NEAR_OPTIMAL=24
ALGORITHM_LP=25
ALGORITHM_LP_BFD=26
ALGORITHM_LP_FFD=27
ALGORITHM_LP_BF=28
ALGORITHM_LP_RANDOM=29


#ALGORITHMS_LISTS
TABU_RANDOM_ALGORITHMS_LIST=[ALGORITHM_TABU_RANDOM_MOVE,ALGORITHM_TABU_RANDOM_SINGLE_SWAP,ALGORITHM_TABU_RANDOM_DOUBLE_SWAP,ALGORITHM_TABU_RANDOM_ALL_MOVES]
TABU_BFD_ALGORITHMS_LIST=[ALGORITHM_TABU_BFD_MOVE,ALGORITHM_TABU_BFD_SINGLE_SWAP,ALGORITHM_TABU_BFD_DOUBLE_SWAP,ALGORITHM_TABU_BFD_ALL_MOVES]
LP_GREEDY_ALGORITHM_LIST=[ALGORITHM_LP_BFD,ALGORITHM_LP_FFD,ALGORITHM_LP_BF,ALGORITHM_LP_RANDOM]

ALGORITHMS_NAMES=[
"BFD_CP",
"FFD",
"BFD_SINGLE_INSTANCE",
"BFD_COMP_PLUS_COMM",
"BFD_COMM",
"BFD_STATELESS",
"BFD_STATEFUL",
"BFA_COMP",
"BF",
"FF",
"RANDOM",
"CP_COMP",
"CP_COMM",
"CP_COMP+COMM",
"CP_2_PASS_STATEFUL",
"CP_2_PASS_STATELESS",
"TABU_BFD_LOWER",
"TABU_BFD_SWAP",
"TABU_BFD_DOUBLE_SWAP",
"TABU_BFD_LOWER+SWAP",
"TABU_RANDOM_MOVE",
"TABU_RANDOM_SWAP",
"TABU_RANDOM_DOUBLE_SWAP",
"TABU_RANDOM_ALL_MOVES",
"NEAR_OPTIMAL",
"LP",
"BFD_LP",
"FFD_LP",
"BF_LP",
"RANDOM_LP",
]
########
marker_dict={ALGORITHM_BFD:"o",
				ALGORITHM_FFD:"+",
				ALGORITHM_BFD_SINGLE_INSTANCE:".",
				ALGORITHM_BFD_COMP_PLUS_COMM:"+",
				ALGORITHM_BFD_comm:"*",
				ALGORITHM_BFD_STATELESS:"+",
				ALGORITHM_BFD_STATEFUL:"_",
				ALGORITHM_BFA_COMP:"*",
				ALGORITHM_BF:"+",
				ALGORITHM_FF:"_",
				ALGORITHM_RANDOM:"+",
				ALGORITHM_CP_COMP:"*",
				ALGORITHM_CP_COMM:"+",
				ALGORITHM_CP_COMP_PLUS_COMM:"*",
				ALGORITHM_CP_STATEFUL_PERC:"+",
				ALGORITHM_CP_STATELESS_PERC:"*",
				ALGORITHM_TABU_BFD_MOVE:"_",
				ALGORITHM_TABU_BFD_SINGLE_SWAP:"o",
				ALGORITHM_TABU_BFD_DOUBLE_SWAP:"*",
				ALGORITHM_TABU_BFD_ALL_MOVES:"_",
				ALGORITHM_TABU_RANDOM_MOVE:"o",
				ALGORITHM_TABU_RANDOM_SINGLE_SWAP:"+",
				ALGORITHM_TABU_RANDOM_DOUBLE_SWAP:"*",
				ALGORITHM_TABU_RANDOM_ALL_MOVES:"o",
				ALGORITHM_NEAR_OPTIMAL:"*",
				ALGORITHM_LP:"*",
				ALGORITHM_LP_BFD:"o",
				ALGORITHM_LP_FFD:"+",
				ALGORITHM_LP_BF:".",
				ALGORITHM_LP_RANDOM:"_"	}
##########
linestyles={ALGORITHM_BFD:"solid",
				ALGORITHM_FFD:"dashdot",
				ALGORITHM_BFD_SINGLE_INSTANCE:"dashed",
				ALGORITHM_BFD_COMP_PLUS_COMM:"dotted",
				ALGORITHM_BFD_comm:"dashdot",
				ALGORITHM_BFD_STATELESS:"dashdot",
				ALGORITHM_BFD_STATEFUL:"dashed",
				ALGORITHM_BFA_COMP:"dotted",
				ALGORITHM_BF:"dotted",
				ALGORITHM_FF:"solid",
				ALGORITHM_RANDOM:"solid",
				ALGORITHM_CP_COMP:"solid",
				ALGORITHM_CP_COMM:"dashed",
				ALGORITHM_CP_COMP_PLUS_COMM:"dashdot",
				ALGORITHM_CP_STATEFUL_PERC:"dashdot",
				ALGORITHM_CP_STATELESS_PERC:"dotted",
				ALGORITHM_TABU_BFD_MOVE:"dashdot",
				ALGORITHM_TABU_BFD_SINGLE_SWAP:"dashed",
				ALGORITHM_TABU_BFD_DOUBLE_SWAP:"dashdot",
				ALGORITHM_TABU_BFD_ALL_MOVES:"dotted",
				ALGORITHM_TABU_RANDOM_MOVE:"dashdot",
				ALGORITHM_TABU_RANDOM_SINGLE_SWAP:"dashed",
				ALGORITHM_TABU_RANDOM_DOUBLE_SWAP:"dashdot",
				ALGORITHM_TABU_RANDOM_ALL_MOVES:"dashed",
				ALGORITHM_NEAR_OPTIMAL:"solid",
				ALGORITHM_LP:"dashdot",
				ALGORITHM_LP_BFD:"solid",
				ALGORITHM_LP_FFD:"dashdot",
				ALGORITHM_LP_BF:"dashed",
				ALGORITHM_LP_RANDOM:"dotted"}
####################
#" Parameters Names"
Display_mapping={
"Total_S_R":"Total Resources",
"Consumed_L_R":"Consumed_L_R",
"Consumed_S_R_per":"Switches Consumed Resources ",
"Consumed_L_R_per":"Bandwidth Consumption (BC)",
"Un_allocated_m_per":"Unallocated Modules %",
"Residual_S_R":"Residual Resources not per",
"Residual_S_R_per":"Residual Resources (RS)",
"Total_m":"Total_m",
"Un_allocated_m":"Un_allocated_m",
"Allocated_m":"Allocated_m",
"allocated_m_Level_0_per":"Level_0_allocated %",
"allocated_m_Level_1_per":"Level_1_allocated %",
"allocated_m_Level_2_per":"Level_2_allocated %",
"Consumed_L_R_weighted":"Consumed_L_R_weighted",
"Consumed_L_R_weighted_per":"Communication Cost (CC) w",
"Overhead_consumed_L_R_weighted_per over total":"Overhead L_R (w) /total",
"Overhead_consumed_L_R_weighted_per over consumed":"Communication Overhead (CO)",
"Overhead_consumed_L_R_weighted":"Overhead_consumed_L_R_weighted",
"Residual_S_level0":"Level_0_Residual Res. %",
"Residual_S_level1":"Level_1_Residual Res. %",
"Residual_S_level2":"Level_2_Residual Res. %",
"Requested_R_per":"Slack Percentage",
"Requested_R_0":"Requested Stateless Per",
"Requested_R_1":"Requested Stateful Per",
"Execution_time":"Execution time",
"Success_rate":"Success rate",
"Allocated_R_per":"Placement Ratio (PR)"
}

##Request orders
ORDERED_BY_COMP_DEC=0
ORDERED_BY_COMM_DEC=1
ORDERED_BY_COMP_DEC_STATELESS_FIRST=2
ORDERED_BY_COMP_DEC_STATEFUL_FIRST=3
ORDERED_BY_COMP_PLUS_COMM=4
ORDERED_BY_COMP_ASC=5
ORDERED_BY_RANDOM=6
ORDERED_BY_RANDOM_STATEFUL_FIRST=7

######## requests 
UN_ALLOCATED_YET=-2
UN_ALLOCATED=-1
#######Unvalid code
NOT_ENOUGHT_COMP=0
NOT_ENOUGHT_BW=1
ENOUGHT=2
###############COST
MAIN_INSTANCE_LEVEL0=0
MAIN_INSTANCE_LEVEL1=1
MAIN_INSTANCE_LEVEL2=2
MONITORING_INSTANCE_LEVEL1=3
MONITORING_INSTANCE_LEVEL2=4
UNALLOCATED_COST=5
LINK_BW_LEVEL1=0
LINK_BW_LEVEL2=1
#######
TABU_MOVE=0
TABU_SINGLE_SWAP=1
#TABU_DOUBLE_SWAP=2
#########
MODULE_SIZE=0
