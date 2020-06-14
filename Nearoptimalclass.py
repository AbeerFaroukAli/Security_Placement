from Allocationclass import *
from docplex.cp.model import CpoModel

class Near_Optimal_Allocation(Allocation):
	
	def __init__(self,scenario,near_optimal_parameters,algorithm):

		super(Near_Optimal_Allocation, self).__init__(scenario,algorithm)
		self.timeout=near_optimal_parameters["timeout"]
		self.trace_log=near_optimal_parameters["trace_log"]
		self.get_near_optimal_allocation()
	
	def get_near_optimal_allocation(self):
		
		unallocated_requests=self.get_unallocated_yet_requests()
		if(unallocated_requests):
			self.get_level_0_allocations()
			#print ("finish level0")
			unallocated_requests=self.get_unallocated_yet_requests()
			if(unallocated_requests):
				self.get_level_1_allocations()
				#print ("finish level1")
				unallocated_requests=self.get_unallocated_yet_requests()
				#print ("unallocated",unallocated_requests)
				if(unallocated_requests):
					self.get_level_2_allocations()
				#	print ("finish level2")

		unallocated_requests=self.get_unallocated_yet_requests()
		for (h,m) in unallocated_requests:
			self.h_m_allocation_dict_dict[h][m]=UN_ALLOCATED

	def get_level_0_allocations(self):
		level=LEVEL0
		for s in Switch.switches_list_in_level[level]:
			self.get_location_optimal_solution_level_0(s)
			
	def get_location_optimal_solution_level_0(self,s):
		
		level=LEVEL0
		requests_list=self.get_unallocated_requests_for_location(switch=s,pod_index=0,level=level)
		if(not requests_list):
			return
		
		cp_locations=[]
		req_cp_locations={}
		used_links={}
		cp_location=self.get_level_0_cp_location(s,0)###only one location
		cp_locations.append(cp_location)
		
		for r in requests_list:
			req_cp_locations[r]=[0]
		
		switches_list=[s]
		self.get_model_solution(switches_list,used_links,requests_list,cp_locations,req_cp_locations)


	def get_location_optimal_solution_level_1(self,pod_index):

		level=LEVEL1
		requests_list=self.get_unallocated_requests_for_location(switch=0,pod_index=pod_index,level=level)
		if(not requests_list):
			return
		
		pod_switches=find_switches_in_pod_in_level(pod_index,level)
		cp_locations=[]
		req_cp_locations={}
		#index=0
		stateless_cp_location=self.get_level_1_cp_location_for_stateless(pod_switches,0)
		cp_locations.append(stateless_cp_location)
		stateful_cp_locations,used_links=self.get_level_1_cp_locations_for_stateful(pod_switches,1)
		
		cp_locations+=stateful_cp_locations
		
		stateful_index_list=range(1,len(cp_locations))

		for r in requests_list:
			(h,m)=r
			if(self.module.modules_list[m].type==STATELESS):
				req_cp_locations[r]=[0]  ###index of stateless CP location =0
			if(self.module.modules_list[m].type==STATEFUL):
				req_cp_locations[r]=[]
				for stateful_index in stateful_index_list:
					req_cp_locations[r].append(stateful_index)
		
		self.get_model_solution(pod_switches,used_links,requests_list,cp_locations,req_cp_locations)
	
	def get_location_optimal_solution_level_2(self):
		
		level=LEVEL2
		requests_list=self.get_unallocated_requests_for_location(switch=0,pod_index=0,level=level)
		if(not requests_list):
			return
		switches_list=Switch.switches_list_in_level[LEVEL2]
		cp_locations=[]
		req_cp_locations={}
		#index=0
		stateless_cp_location=self.get_level_2_cp_location_for_stateless(0)
		cp_locations.append(stateless_cp_location)
		#index=1
		stateful_cp_locations,used_links=self.get_level_2_cp_locations_for_stateful(1)
		cp_locations+=stateful_cp_locations
		stateful_index_list=range(1,len(cp_locations))
		
		
		for r in requests_list:
			(h,m)=r
			if(self.module.modules_list[m].type==STATELESS):
				req_cp_locations[r]=[0]  ###index of stateless CP location =0
			if(self.module.modules_list[m].type==STATEFUL):
				req_cp_locations[r]=[]
				for stateful_index in stateful_index_list:
					req_cp_locations[r].append(stateful_index)
		
		self.get_model_solution(switches_list,used_links,requests_list,cp_locations,req_cp_locations)
	

	
	
	def get_model_solution(self,switches_list,links_list,requests_list,cp_locations,req_cp_locations):

		#print ("before modle soution",switches_list,links_list,requests_list,len(cp_locations),req_cp_locations)
		cp_model = CpoModel()
		X=cp_model.binary_var_dict([(r, l) for r in (requests_list) for l in req_cp_locations[r]], name="X")
		##################
		for r in requests_list:
			cp_model.add(cp_model.sum(X[(r,l)] for l in req_cp_locations[r])<=1)
		
		def cp_switches_cost(r,l,s):
			if s in cp_locations[l].switches:
				return 	self.scenario.requests_dict[r].switches_cost_list[cp_locations[l].switches[s]]
			else:
				print ("error here")
				exit()
				return 0
		
		def cp_links_cost(r,l,lk):
			if lk in cp_locations[l].links:
				return 	self.scenario.requests_dict[r].link_cost*cp_locations[l].links[lk]
			else:
				return 0 
		for s in switches_list:
			cp_model.add(cp_model.sum(cp_switches_cost(r,l,s)*X[(r,l)] for r in requests_list for l in req_cp_locations[r]) <=self.switches_online_capacity[s] )
		for lk in links_list:
			if(self.tree.links_dict[lk].level!=LEVEL2):
				cp_model.add(cp_model.sum(cp_links_cost(r,l,lk)*X[(r,l)] for r in requests_list for l in req_cp_locations[r])<=self.links_online_capacity[lk])

		S_Obj=cp_model.sum(self.scenario.requests_dict[r].switches_cost_list[cp_locations[l].switches[s]]*X[(r,l)] for r in requests_list for l in req_cp_locations[r] for s in cp_locations[l].switches)
		cp_model.maximize(S_Obj)
		msol =cp_model.solve(TimeLimit=self.timeout,trace_log=self.trace_log,Workers=2,FailureDirectedSearchEmphasis=1)
		self.update_allocation_after_solving_near_optimal(X,msol,cp_locations)


	def update_allocation_after_solving_near_optimal(self,X,solution,locations_list):
		##########this function will update self allocation with result from x and soution
		############find req_allocation for each x(h,m)=1
		########by creating  req_allocation for each location with x(h,m)=1
		if(not solution):
			print ("Coudn't reach solution in update after solving")
			exit()
			# hase update results
		for r,location_index in X:
			(h,m)=r
			cp_location=locations_list[location_index]
			if solution[X[(r,location_index)]]==1:
				if ((self.module.modules_list[m].type==STATEFUL) and (cp_location.level==LEVEL2)):
					req_allocation=self.get_complete_valid_location_for_level_1_2_after_cp(h,m,cp_location)
				elif((self.module.modules_list[m].type==STATELESS) or (cp_location.level!=LEVEL2)):
					req_allocation=self.create_req_allocation_for_cp_location(h,m,cp_location)
				else:
					print ("error in update near optimal")
					exit()
				self.update_allocation(h,m,req_allocation)
				
	def get_level_1_allocations(self):
		
		for pod_index in range(self.tree.no_of_pods):
			self.get_location_optimal_solution_level_1(pod_index)
	
	def get_level_2_allocations(self):
		self.get_location_optimal_solution_level_2()

	def get_unallocated_requests_for_location(self,switch,pod_index,level):
		
		unallocated_requests=self.get_unallocated_yet_requests()
		requests_list=[]
		if(level==LEVEL0):
			for (h,m) in unallocated_requests:
				if switch in self.tree.hosts_list[h].parent_switches[LEVEL0]:
					requests_list.append((h,m))
		elif(level==LEVEL1):
			for (h,m) in unallocated_requests:
				if(self.tree.hosts_list[h].pod_index==pod_index):
					requests_list.append((h,m))
		elif(level==LEVEL2):
			for (h,m) in unallocated_requests:
				requests_list.append((h,m))
		else:
			print ("error in get unallocated requests")
			exit()
					
		return requests_list

	def get_level_0_cp_location(self,s,start_index):
		level=LEVEL0
		links={}
		routes={}
		index=start_index
		switches={s:MAIN_INSTANCE_LEVEL0}
		cp_location=CP_Location(index,level,switches,links,routes)
		return cp_location
	
	def get_level_1_cp_location_for_stateless(self,pod_switches_list,start_index):
		level=LEVEL1
		links={}
		routes={}
		index=start_index
		switches={s:MAIN_INSTANCE_LEVEL1 for s in pod_switches_list}
		cp_location=CP_Location(index,level,switches,links,routes)
		return cp_location

	def get_level_2_cp_location_for_stateless(self,start_index):
		###########Level 2 location (only one)
		switches_list=Switch.switches_list_in_level[LEVEL2]
		level=LEVEL2
		links={}
		routes={}
		index=start_index

		switches={s:MAIN_INSTANCE_LEVEL2 for s in switches_list }
		cp_location=CP_Location(index,level,switches,links,routes)
		return cp_location
	
	def get_level_1_cp_locations_for_stateful(self,pod_switches,start_index):

		level=LEVEL1
		cp_locations=[]
		index=start_index
		used_links={}
		for switch in pod_switches:
			switches={}
			################Resources cost  swicthes={}
			for s1 in pod_switches:
				switches[s1]=MONITORING_INSTANCE_LEVEL1
			switches[switch]=MAIN_INSTANCE_LEVEL1
			link_share=Switch.no_of_switches_per_pod#########This level have double traffic and consq double communication share
			#######################comm cost
			new_switches_list=deepcopy(pod_switches)
			new_switches_list.remove(switch)
			
			comm_routes_dict=self.get_all_routes_to_switch(switch,new_switches_list)
			############create combination for all routes
			numeric_mertic_combination=self.get_numeric_combination_generator_order_by_new_switch_list(comm_routes_dict,switch,new_switches_list)
			##get links allocation and communication cost
			for combination in numeric_mertic_combination:
				links={}
				routes=[]
				for j,perm in enumerate(combination):
					route=comm_routes_dict[new_switches_list[j]][perm]
					route_links=find_links_for_route(route)
					for link in route_links:
						used_links[link]=0
						if link in links:
							links[link]+=link_share
						else:
							links[link]=link_share
					routes.append(route)
				cp_location=CP_Location(index,level,switches,links,routes)
				cp_locations.append(cp_location)
				index+=1
		return cp_locations,used_links
	
	def get_level_2_cp_locations_for_stateful(self,start_index):
		
		switches_list=Switch.switches_list_in_level[LEVEL2]
		cp_locations=[]
		index=start_index
		links={}
		links['EXTRA_LINK_LEVEL_1']=0
		links['EXTRA_LINK_LEVEL_2']=0
		level=LEVEL2
		routes=[]
		#############Calaculate linkshare in level2
		link_share_level_1=0
		link_share_level_2=0
		comm_routes_dict=self.get_one_route_to_switch(switches_list[0],switches_list[1:])
		for route in comm_routes_dict:
			route_links=find_links_for_route(comm_routes_dict[route])
			for link in route_links:
				if(self.tree.links_dict[link].level==LEVEL1):
					link_share_level_1+=1
				elif(self.tree.links_dict[link].level==LEVEL2):
					link_share_level_2+=1
				else:
					print ("unknown level in links cp main class")
					exit()
		##################################
		links['EXTRA_LINK_LEVEL_1']=link_share_level_1
		links['EXTRA_LINK_LEVEL_2']=link_share_level_2
		for switch in switches_list:
			switches={}
			new_switches_list=deepcopy(switches_list)
			new_switches_list.remove(switch)
			########################
			################Resources cost  swicthes={}
			for s1 in switches_list:
				switches[s1]=MONITORING_INSTANCE_LEVEL2
			switches[switch]=MAIN_INSTANCE_LEVEL2
			#######################comm cost
			cp_location=CP_Location(index,level,switches,links,routes)
			cp_locations.append(cp_location)
			index+=1
		return cp_locations,{}
if __name__ == '__main__':
	
	Fat_tree={"k":6}
	files={"path":"Result/"}
	#####writing_mode='w' or 'a'====> w mean erase old files while 'a' mean extend  already exist files
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	modules={"max_size_of_module":switches["rack_capacity"],"stateless_modules_per":1,
	"number_of_modules":10,"modules_size_mean_per":0.5,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.5,"comm_cost_stdev_per":0.1}


	scenario={"host_modules_request_rate":1,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
	#parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	#"over_ratio_weighted_only_over_links","over_ratio_weighted_All_links","over_ratio_only_over_links","over_ratio_All_links","Requested_R_per"]

	cp={"timeout":50,"trace_log":True}
	near_optimal={"timeout":100,"trace_log":False}


	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	algorithm=ALGORITHM_NEAR_OPTIMAL

	A=Near_Optimal_Allocation(scenario=S,near_optimal_parameters=near_optimal,algorithm=algorithm)
	print ("OK")
	#print vars(A)
						
