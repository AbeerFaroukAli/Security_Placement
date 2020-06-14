from Allocationclass import *
class Single_Instance_Allocation(Allocation):
	
	def __init__(self,scenario,algorithm):
		
	
		super(Single_Instance_Allocation, self).__init__(scenario,algorithm)
		add_to_file(self,'a',"\nStart allocation process for "+str(ALGORITHMS_NAMES[algorithm]),self.tree.trace,False)
		
		####################hosts_online_parents_in_level {h1:[[1],[4,5]],[9,8,6,9]}
		self.hosts_online_parents_per_level={}
		self.hosts_online_flow_route_dict_dict_tuple={}
		self.init_hosts_online_data_structure()
		self.get_one_instnce_allocation()

	def	init_hosts_online_data_structure(self):
		#self.hosts_online_flow_route_dict_dict_tuple={h1:{(s1,s5,s6):3),},{}],...
		for h in range(Host.no_of_hosts):
			route_flow_size=self.scenario.host_traffic_demand_dict[h]/len(Switch.switches_list_in_level[LEVEL2])
			self.hosts_online_parents_per_level[h]=deepcopy(self.tree.hosts_list[h].parent_switches)
			self.hosts_online_flow_route_dict_dict_tuple[h]={}
			for route in self.tree.hosts_list[h].ECMP_traffic_routes:
				self.hosts_online_flow_route_dict_dict_tuple[h][tuple(route)]=route_flow_size


	def get_one_instnce_allocation(self):		
		########################	
		##### request list tuple(type,comp cost,comm cost,comp+comm cost,host,module )
		request_list=self.sort_requests()
		for mtype,comp_cost,comm_cost,total_cost,h,m in request_list:
			self.get_allocation(h,m)
		self.check_host_flows_and_modules()
	
	def get_allocation(self,h,m):
		
		if(self.algorithm!=ALGORITHM_BFD_SINGLE_INSTANCE):
			print ("Error in get allocation single instance")
			exit()
		
		levelfound=False
		levels_list=[LEVEL0,LEVEL1,LEVEL2]
		
		if(self.algorithm==ALGORITHM_FF or self.algorithm==ALGORITHM_FFD):
			shuffle(levels_list)
		
		add_to_file(self,'a',"\n["+str(h)+","+str(m)+"] type "+str(self.module.modules_list[m].type),self.tree.trace,False)
		
		for level in levels_list:
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

	def find_valid_allocation(self,h,m,level):
		
		#change to communication cost,computing cost,steering cost
		#Flow_replacements_list_tuple [(oldpath,newpath,size)]
		#parent_replacement_list_tuple=[(1,s2),(2,s5),....]
		#req_baseline_cost=self.scenario.requests_h_m_dict_dict[h][m].baseline_cost
		#req_traffic_cost=self.scenario.requests_h_m_dict_dict[h][m].traffic_cost
		#req_comm_cost=self.scenario.requests_h_m_dict_dict[h][m].comm_cost
		allocation_comp_cost={}
		allocation_comm_cost=[]
		flow_replacement=[]
		parent_replacement=[]
		req_allocation=0

		switches_list=self.tree.hosts_list[h].parent_switches[level]
		random_switches_list=sorted(switches_list, key=self.switches_online_capacity.get,reverse=True)
		#shuffle(random_switches_list)

		switch_cost=self.scenario.requests_h_m_dict_dict[h][m].switches_cost_list[MAIN_INSTANCE_LEVEL0]
		 ###  level 0 case + level1 and 2 after conversion
		if len(self.hosts_online_parents_per_level[h][level])==1:
			#####################################Switches cost
			switch=self.hosts_online_parents_per_level[h][level][0]  ###############should be one
			allocation_comp_cost={switch:switch_cost}
			req_allocation=Request_Allocation(level,allocation_comp_cost,allocation_comm_cost)
			valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
			return valid,req_allocation
							
		if level==LEVEL1:
			for switch in random_switches_list:
				#####################################Switches cost
				allocation_comp_cost={switch:switch_cost}
			#################################replacements cost for all switches otherthan s
				flow_replacement=self.move_traffic_through_switch_in_level(h,switch,level)
				parent_replacement=[(level,switch)]
			#################Allocation
				req_allocation=Request_Allocation(level,allocation_comp_cost,allocation_comm_cost,flow_replacement,parent_replacement)
				valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
				if(valid):
					return valid,req_allocation
	
		if level==LEVEL2:
			#####case  when level 1 is already converted
			if len(self.hosts_online_parents_per_level[h][LEVEL1])==1:
				for switch in random_switches_list:   ###Level 2 parent switches
					#direct neighboure with single parent at level 1
					if switch in self.tree.graph[self.hosts_online_parents_per_level[h][LEVEL1][0]]: ###Level 2 parent switches which has direct connection with the level 1 only parent
						#print (switch)
						#####################################Switches cost
						allocation_comp_cost={switch:switch_cost}
						#################################replacements cost for all switches otherthan s
						flow_replacement=self.move_traffic_through_switch_in_level(h,switch,level)
						#################Allocation
						parent_replacement=[(level,switch)]
						
						req_allocation=Request_Allocation(level,allocation_comp_cost,allocation_comm_cost,flow_replacement,parent_replacement)
						valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
						if(valid):
							return valid,req_allocation
			else:
				for s1 in self.hosts_online_parents_per_level[h][LEVEL1]:
					for s in random_switches_list:   ###Level 2 parent switches
						if s in self.tree.graph[s1]: ###Level 2 parent switches which has direct connection with the level 1 only parent
							#####################################Switches cost
							allocation_comp_cost={s:switch_cost}
							#################################replacements cost for all switches otherthan s
							flow_replacement=self.move_traffic_through_switch_in_level(h,s,level)
							parent_replacement=[(level,s),(1,s1)]
							req_allocation=Request_Allocation(level,allocation_comp_cost,allocation_comm_cost,flow_replacement,parent_replacement)
							valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
							if(valid):
								return valid,req_allocation		
		
		return valid,req_allocation
	
	def move_traffic_through_switch_in_level(self,h,s,level):
		
		#self.check_host_flows_and_modules()
		#Flow_replacements_list_tuple [(oldpath,newpath,size)]
		#self.hosts_online_flow_route_dict_dict_tuple={h1:{(s1,s5,s6):3),},{}],...
		flow_replacements_list_tuple=[]
		for path in self.hosts_online_flow_route_dict_dict_tuple[h]:
			if(s in path):
				continue
				#if s1 in path:
			size=self.hosts_online_flow_route_dict_dict_tuple[h][path]
			Part_1=shortest_path(self.tree.graph,path[0],s)
			Part_2=shortest_path(self.tree.graph,s,path[-1])
			newpath=tuple(Part_1)+tuple(Part_2[1:])
			flow_replacements_list_tuple.append((path,newpath,size))
		return flow_replacements_list_tuple


if __name__ == '__main__':
	
	Fat_tree={"k":6}
	#####writing_mode='w' or 'a'====> w mean erase old files while 'a' mean extend  already exist files
	files={"path":"Result/"}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,1]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	modules={"max_size_of_module":switches["rack_capacity"],"stateless_modules_per":0.5,
	"number_of_modules":6,"modules_size_mean_per":0.5,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.5,"comm_cost_stdev_per":0.1}

	scenario={"host_modules_request_rate":2,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
	parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	"over_ratio_weighted_only_over_links","over_ratio_weighted_All_links","over_ratio_only_over_links","over_ratio_All_links","Requested_R_per"]

	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	

	algorithm=ALGORITHM_BFD_SINGLE_INSTANCE
	A=Single_Instance_Allocation(scenario=S,algorithm=algorithm)
	

	print ("OK")
	#print vars(A)
						
