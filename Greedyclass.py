from Allocationclass import *

class Greedy_Allocation(Allocation):
	
	def __init__(self,scenario,algorithm):

		super(Greedy_Allocation, self).__init__(scenario,algorithm)
		self.get_greedy_allocation()

	def get_greedy_allocation(self):		
		##### request list tuple(type,comp cost,comm cost,comp+comm cost,host,module )
		add_to_file(self,'a',"\nStart allocation process for "+str(ALGORITHMS_NAMES[self.algorithm]),self.tree.trace,False)

		request_list=self.sort_requests()
		for mtype,comp_cost,comm_cost,total_cost,h,m in request_list:
			self.get_allocation(h,m)
		add_to_file(self,'a',"Allocation for "+str(ALGORITHMS_NAMES[self.algorithm])+" Completed",self.tree.trace,False)
			
	def get_allocation(self,h,m):
		
		levelfound=False
		levels_list=[LEVEL0,LEVEL1,LEVEL2]
		if(self.algorithm in [ALGORITHM_FF,ALGORITHM_FFD,ALGORITHM_RANDOM,ALGORITHM_LP_FFD,ALGORITHM_LP_RANDOM]):
			shuffle(levels_list)
		
		add_to_file(self,'a',"\n["+str(h)+","+str(m)+"] type "+str(self.module.modules_list[m].type),self.tree.trace,False)
		
		for level in levels_list:
			if(self.module.modules_list[m].type==STATEFUL) and (level!=LEVEL0) and (self.algorithm in LP_GREEDY_ALGORITHM_LIST):
				continue
			levelfound,req_allocation=self.find_valid_allocation(h,m,level)
			if(levelfound):
				self.update_allocation(h,m,req_allocation)
				return
			else:
				#no valid locations found in this level
				continue
			
		if(levelfound==False):
			## no valid allocations found at all levels
			add_to_file(self,'a',"\n No valid Allocation found",self.tree.trace,False)
			self.h_m_allocation_dict_dict[h][m]=UN_ALLOCATED
		
		
	
if __name__ == '__main__':
	
	files={"path":"Result/"}
	Fat_tree={"k":6}
	#####writing_mode='w' or 'a'====> w mean erase old files while 'a' mean extend  already exist files
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.9,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["rack_capacity"]
	modules={"max_size_of_module":switches["rack_capacity"],"stateless_modules_per":0.5,
	"number_of_modules":30,"modules_size_mean_per":0.9,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.7,"comm_cost_stdev_per":0.1}

	scenario={"host_modules_request_rate":1,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
	parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	"over_ratio_weighted_only_over_links","over_ratio_weighted_All_links","over_ratio_only_over_links","over_ratio_All_links","Requested_R_per"]

	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	algorithm=ALGORITHM_BFD
	A=Greedy_Allocation(scenario=S,algorithm=algorithm)
	
	
	print ("OK")
	#print vars(A)
						
