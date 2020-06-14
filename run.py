from Greedyclass import*
from Single_instanceclass import *
from Tabuclass import *
from Nearoptimalclass import *
from CPclass import *
from LP import *
import sys

class Run(object):

	def __init__(self,fattree_parameters,switches_parameters,links_parameters,hosts_parameters,modules_parameters,scenario_paramters,
				cp_parameters,tabu_parameters,near_optimal_parameters,
				files,
				greedy_algorithms_list,cp_algorithms_list,parameters_list,run_no,filename,trace):
						
		#############################################################valid scenario
		## prevent running a scenario with 0 requests
		run_tree=FatTree(fattree_parameters,switches_parameters,links_parameters,hosts_parameters,files_parameters=files,trace=trace)
		my_file=file_class(filename)
		while(1):
			
			run_modules=Modules_Pool(tree=run_tree,modules_parameters=modules_parameters)
			run_scenario=Scenario(module=run_modules,scenario_parameters=scenario_paramters,scenario_object={},class_type={})
			if  run_scenario.requests_dict:####meaning: requests is not 0
				if scenario_paramters["host_modules_request_rate"] <=3:
					break
				if(modules_parameters["stateless_modules_per"]==0.5):
					stateless_per=run_scenario.requested_R_stateless/run_scenario.requested_R
					stateful_per=run_scenario.requested_R_stateful/run_scenario.requested_R
					#print (stateless_per,stateful_per)
					if((stateless_per>stateful_per+0.03) or(stateless_per<stateful_per-0.03)):
						continue
				break
		##########################################All results of all algorirthms of this  run
		self.file=run_tree.files_path+"run.txt"
		#self.file=run_files["files_path"]+run_files["file_name"]
		self.run_result=[] 
		if(run_no==0):
			print ("\nStart runs")
			add_to_file(self,'w',"Start runs ",run_tree.trace,False)
		print ("\nRun=",run_no)
		BFD_allocation=[]
		for algorithm in greedy_algorithms_list:
			print ("\nAlgo=",ALGORITHMS_NAMES[algorithm]," M_mean=",modules_parameters["modules_size_mean_per"],"F_mean=",hosts_parameters["host_flow_rate_mean_per"]," type1_p=",modules_parameters["stateless_modules_per"]," request_rate=",scenario_paramters["host_modules_request_rate"]," k=",fattree_parameters["k"]," max_of_m=",round(modules_parameters["max_size_of_module"],0))
			if(algorithm==ALGORITHM_BFD_SINGLE_INSTANCE):
				algorithm_allocation=Single_Instance_Allocation(scenario=run_scenario,algorithm=algorithm)
			elif(algorithm in TABU_RANDOM_ALGORITHMS_LIST+TABU_BFD_ALGORITHMS_LIST):
				algorithm_allocation=TABU_Allocation(scenario=run_scenario,algorithm=algorithm,tabu_parameters=tabu_parameters)
			elif(algorithm==ALGORITHM_NEAR_OPTIMAL):
				algorithm_allocation=Near_Optimal_Allocation(scenario=run_scenario,near_optimal_parameters=near_optimal_parameters,algorithm=algorithm)
			elif(algorithm in [ALGORITHM_BFD,ALGORITHM_FFD,ALGORITHM_BFD_COMP_PLUS_COMM,ALGORITHM_BFD_comm,ALGORITHM_BFD_STATELESS,ALGORITHM_BFD_STATEFUL,ALGORITHM_BFA_COMP,ALGORITHM_BF,ALGORITHM_FF,ALGORITHM_RANDOM]):
				algorithm_allocation=Greedy_Allocation(scenario=run_scenario,algorithm=algorithm)
			elif(algorithm ==ALGORITHM_LP):
				algorithm_allocation=LP_Allocation(scenario=run_scenario,algorithm=algorithm)
			elif(algorithm in LP_GREEDY_ALGORITHM_LIST):
				algorithm_allocation=Greedy_Allocation(scenario=run_scenario,algorithm=algorithm)
			else:
				print ("Error in run undefined algorithm")
				exit()
			Res=algorithm_allocation.get_results(parameters_list)
			self.print_result(Res,parameters_list)
			self.run_result.append(Res)
			add_to_file(my_file,"a",str(Res)+"\n",True,False)
			add_to_file(self,'a',"\nk="+str(run_tree.k)+" run#="+str(run_no)+" Allocation for " +str(ALGORITHMS_NAMES[algorithm_allocation.algorithm]),algorithm_allocation.tree.trace,False)
			self.print_allocation(algorithm_allocation)
		algorithm_allocation=[]
			
		for algorithm in cp_algorithms_list:
			print ("\nAlgo=",ALGORITHMS_NAMES[algorithm]," M_mean=",modules_parameters["modules_size_mean_per"],"F_mean=",hosts_parameters["host_flow_rate_mean_per"]," type1_p=",modules_parameters["stateless_modules_per"]," request_rate=",scenario_paramters["host_modules_request_rate"]," k=",fattree_parameters["k"]," max_of_m=",round(modules_parameters["max_size_of_module"],0))
			#add_to_file(self,'a',"\nrun#="+str(run_no)+" Start allocation process for "+str(ALGORITHMS_NAMES[algorithm]),run_tree.trace,False)
			algorithm_allocation=CP_Allocation(scenario=run_scenario,algorithm=algorithm,cp_parameters=cp_parameters,scenario_parameters=scenario_paramters,switches_online_capacity={},links_online_capacity={})
			Res=algorithm_allocation.get_new_results(parameters_list)
			self.print_result(Res,parameters_list)
			add_to_file(m,"a",str(Res)+"\n",True,False)
			self.run_result.append(Res)
			add_to_file(self,'a',"\nk="+str(run_tree.k)+" run#="+str(run_no)+" Allocation for " +str(ALGORITHMS_NAMES[algorithm_allocation.algorithm]),algorithm_allocation.tree.trace,False)
			self.print_allocation(algorithm_allocation)
			algorithm_allocation=[]
			#Res=[]
	
	def print_result(self,R,parameters_list):
		parameter_list_displayed={
		"Overhead_consumed_L_R_weighted_per over consumed":"L_Overhead"
		,"Residual_S_R":"Res_R"
		,"Consumed_S_R":"Consumed_R"
		,"Un_allocated_m_per":"Un_all m "
		#,"allocated_m_Level_2_per":"m_Level_2"
		,"Execution_time":"time"
		}
		for par in parameter_list_displayed:
			print (parameter_list_displayed[par],"=",round(R[parameters_list.index(par)],2),end=" ") 
	
	def print_allocation(self,allocation):
		
		for h in allocation.h_m_allocation_dict_dict:
			for m in allocation.h_m_allocation_dict_dict[h]:
				if (allocation.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED):
					add_to_file(self,"a","\n "+str(h)+" "+str(m)+" type="+str(allocation.module.modules_list[m].type)
				+" Unallocated=",allocation.tree.trace,False)
					continue
				
				req_allocation=allocation.h_m_allocation_dict_dict[h][m]
				add_to_file(self,"a","\n "+str(h)+" "+str(m)+" level="+str(req_allocation.level)+" type="+str(allocation.module.modules_list[m].type)
				+" baseline_cost="+str(allocation.scenario.requests_h_m_dict_dict[h][m].baseline_cost)
				+" traffic_cost="+str(allocation.scenario.requests_h_m_dict_dict[h][m].traffic_cost)	
				+" comm_cost="+str(allocation.scenario.requests_h_m_dict_dict[h][m].comm_cost)
				+" allocation_comp_cost="+str(req_allocation.switches_cost_dict)
				+" allocation_comm_cost="+str(req_allocation.links_cost_list),allocation.tree.trace,False)

		add_to_file(self,"a","\n COMP="+str(sum(allocation.switches_online_capacity.values())),allocation.tree.trace,False)
		add_to_file(self,"a"," COMM="+str(sum(allocation.links_online_capacity.values())),allocation.tree.trace,False)

class file_class(object):
	def __init__(self,file):
		self.file=file					
if __name__ == '__main__':
	
	
	files={"path":"Result/"}
	Fat_tree={"k":6}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.7,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	modules={"max_size_of_module":switches["rack_capacity"],"stateless_modules_per":0.5,
	"number_of_modules":5,"modules_size_mean_per":0.7,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.5,"comm_cost_stdev_per":0.1}

	scenario={"host_modules_request_rate":1,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
	cp={"timeout":300,"trace_log":True,"workers":2}
	near_optimal={"timeout":50,"trace_log":False}
	tabu={"iterations":200,"tabu_list_len":50}
	greedy_algorithms_list=[ALGORITHM_BFD]
	cp_algorithms_list=[ALGORITHM_CP_STATEFUL_PERC]
	
	
	parameters_list=["Total_S_R","Residual_S_R","Consumed_S_R","Requested_R_per",
	"Total_L_R","Total_L_R_weighted","Consumed_L_R","Consumed_L_R_weighted","Overhead_consumed_L_R_weighted",
	"Consumed_L_R_weighted_per","Overhead_consumed_L_R_weighted_per over consumed","Overhead_consumed_L_R_weighted_per over total",
	"Consumed_L_R_per",
	"Residual_S_R_per","Consumed_S_R_per",
	"Total_m","Un_allocated_m","Allocated_m","Un_allocated_m_per",
	"allocated_m_Level_0_per","allocated_m_Level_1_per","allocated_m_Level_2_per","Residual_S_level0",
	"Residual_S_level1","Residual_S_level2",
	"Requested_R_0","Requested_R_1","Execution_time","Success_rate"
	]
	
	R=Run(Fat_tree,switches,links,hosts,modules,scenario,cp,tabu,near_optimal,
			files,
			greedy_algorithms_list=greedy_algorithms_list,cp_algorithms_list=cp_algorithms_list,
			parameters_list=parameters_list,run_no=0,filename="Result/runs.txt",trace=True)
	print ("ok")
