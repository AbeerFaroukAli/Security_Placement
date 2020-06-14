from run import *

#####################Run Parameters
Runs=10
Trace=False
files={"path":"Result/"}
Fat_Tree_parameters={"k":6}
Switches_parameters={"rack_capacity":100,"capacity_mode":"VARIABLE"}
Links_parameters={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
Hosts_parameters={"host_max_traffic_rate":Links_parameters["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.7,"host_flow_rate_stdev_per":0.1}
Scenario_parameters={"host_modules_request_rate":4,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
Modules_parameters={"max_size_of_module":Switches_parameters["rack_capacity"]/4,"stateless_modules_per":0.5,"number_of_modules":20,"modules_size_mean_per":0.5,"modules_size_stdev_per":0.1,"comm_cost_mean_per":0.2,"comm_cost_stdev_per":0.1}
CP_parameters={"timeout":4000,"trace_log":False,"workers":2}
Tabu_parameters={"iterations":200,"tabu_list_len":50}
Near_Optimal_parameters={"timeout":200,"trace_log":False}	
parameters_list=["Total_S_R","Residual_S_R","Consumed_S_R","Requested_R_per","Total_L_R","Total_L_R_weighted","Consumed_L_R","Consumed_L_R_weighted","Overhead_consumed_L_R_weighted","Consumed_L_R_weighted_per","Overhead_consumed_L_R_weighted_per over consumed","Overhead_consumed_L_R_weighted_per over total","Consumed_L_R_per","Residual_S_R_per","Consumed_S_R_per","Total_m","Un_allocated_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_0_per","allocated_m_Level_1_per","allocated_m_Level_2_per","Residual_S_level0","Residual_S_level1","Residual_S_level2","Requested_R_0","Requested_R_1","Execution_time","Success_rate","Allocated_R_per"]
#algorithms_list=[ALGORITHM_BFD,ALGORITHM_FFD,ALGORITHM_BFD_SINGLE_INSTANCE,ALGORITHM_BFD_STATELESS,ALGORITHM_BFD_STATEFUL,ALGORITHM_RANDOM,ALGORITHM_TABU_BFD_MOVE,ALGORITHM_TABU_BFD_SINGLE_SWAP,ALGORITHM_TABU_BFD_ALL_MOVES,ALGORITHM_TABU_RANDOM_MOVE,ALGORITHM_TABU_RANDOM_SINGLE_SWAP,ALGORITHM_TABU_RANDOM_ALL_MOVES,ALGORITHM_NEAR_OPTIMAL,ALGORITHM_LP,ALGORITHM_LP_BFD,ALGORITHM_LP_RANDOM]
algorithms_list=[ALGORITHM_BFD,ALGORITHM_FFD]
#cp_algorithms_list=[ALGORITHM_CP_COMP,ALGORITHM_CP_COMM,ALGORITHM_CP_COMP_PLUS_COMM,ALGORITHM_CP_STATELESS_PERC,ALGORITHM_CP_STATEFUL_PERC]
cp_algorithms_list=[]
Module_size_mean_list=[0.1,0.3,0.5,0.7,0.8,0.9]		
	
##################Create Output file by time
output_file_name="Result/Output.txt"	
##################Write simulation parameters
add_to_output_file(output_file_name,"w",
	"FatTree="+str(Fat_Tree_parameters)+
	"\nSwitches="+str(Switches_parameters)+
	"\nLinks="+str(Links_parameters)+
	"\nModules="+str(Modules_parameters)+
	"\nHosts="+str(Hosts_parameters)+
	"\nScenario="+str(Scenario_parameters)+
	"\nCP="+str(CP_parameters)+
	"\nTabu="+str(Tabu_parameters)+
	"\nNear_Optimal="+str(Near_Optimal_parameters)+
	"\nRuns="+str(Runs)+
	"\nModule_size_mean_list="+str(Module_size_mean_list)+
	"\nparameters_list="+str(parameters_list)+
	"\nalgorithms_list="+str(algorithms_list+cp_algorithms_list)+"\n",False)
	
###################Main loop
for mean in Module_size_mean_list:
	for run_no in range(Runs):
		Modules_parameters["modules_size_mean_per"]=mean
		add_to_output_file(output_file_name,"a","Run "+str(run_no)+"\n",False)
		R=Run(Fat_Tree_parameters,Switches_parameters,Links_parameters,Hosts_parameters,Modules_parameters,
			Scenario_parameters,CP_parameters,Tabu_parameters,
			Near_Optimal_parameters,files,
			greedy_algorithms_list=algorithms_list,cp_algorithms_list=cp_algorithms_list,
			parameters_list=parameters_list,run_no=run_no,filename=output_file_name,trace=Trace)
	
print ("Simualtion Completed")

    
 
