from Allocationclass import *
from docplex.cp.model import CpoModel

		
class CP_Main_Allocation(Allocation):
	
	
	def __init__(self,scenario,algorithm,cp_parameters,switches_online_capacity,links_online_capacity):
		
		super(CP_Main_Allocation, self).__init__(scenario,algorithm)
		####################################################requestes scenario Data structure(modules)
		#####Locations   list of locations objects
		###########The following if is for the case where two phase of CP
		if(switches_online_capacity):
			self.switches_online_capacity=switches_online_capacity
			self.links_online_capacity=links_online_capacity
		
		self.cp_locations=[]
		self.cp_locations_index=0
		#############self.req_cp_locations={(h,m):[] 
		self.req_cp_locations={}
		self.cp_links_weight={}

		self.build_CP_main_allocation()

		
	def update_allocation_after_solving_cp(self,X,solution,locations_list):
		##########this function will update self allocation with result from x and soution
		############find req_allocation for each x(h,m)=1
		########by creating  rwq_allocation for each location with x(h,m)=1
		level_1_2_allocation_list=[]
		if(solution):
			# hase update results
			for r,location_index in X:
				(h,m)=r
				cp_location=locations_list[location_index]

				if solution[X[(r,location_index)]]==1:
					if ((self.module.modules_list[m].type==STATEFUL) and (cp_location.level in [LEVEL1,LEVEL2])):
						level_1_2_allocation_list.append((r,location_index))
						#req_allocation=get_complete_valid_location_for_level2_after_cp(h,m,location)
					else:
						req_allocation=self.create_req_allocation_for_cp_location(h,m,cp_location)
						self.update_allocation(h,m,req_allocation)
					
		else:
			print (self.switches_online_capacity)
			print ([x for x in self.scenario.requests_dict])
			print (self.algorithm)
			for x in self.cp_locations:
				print (x.switches)
			print (self.req_cp_locations)
			#print self.request_dict
			print ("Coudn't reach solution in update after solving", self.algorithm)
			exit()
		for (r,location_index) in level_1_2_allocation_list:
			(h,m)=r
			cp_location=locations_list[location_index]
			req_allocation=self.get_complete_valid_location_for_level_1_2_after_cp(h,m,cp_location)
			self.update_allocation(h,m,req_allocation)
			
	def build_CP_main_allocation(self):		
		########################	
		add_to_file(self,'a',"Creating CP for algorithm="+str(ALGORITHMS_NAMES[self.algorithm]),self.tree.trace,False)
		self.build_cp_locations()
		self.build_cp_main_model()

	def build_cp_main_model(self):
		total_R=sum(self.switches_online_capacity.values())
		total_L=sum(self.links_online_capacity.values())
		######### Create CPO model
		self.cpmodel = CpoModel()
		self.X=self.cpmodel.binary_var_dict([(r, l) for r in (self.scenario.requests_dict) for l in self.req_cp_locations[r]], name="X")	
		##################################sum equal 1 constraints   ### single instnace and must have allocation
		for r in self.scenario.requests_dict:
			self.cpmodel.add(self.cpmodel.sum(self.X[(r,l)] for l in self.req_cp_locations[r])==1)
	#	print ("CP sum=1 constraint created")
		#######################Function	
		def cp_switches_cost(r,l,s):
			if s in self.cp_locations[l].switches:
				return 	self.scenario.requests_dict[r].switches_cost_list[self.cp_locations[l].switches[s]]
			else:
				return 0
		
		def cp_links_cost(r,l,lk):
			if lk in self.cp_locations[l].links:
				return 	self.scenario.requests_dict[r].link_cost*self.cp_locations[l].links[lk]
			else:
				return 0
		for s in self.switches_online_capacity:
			self.cpmodel.add(self.cpmodel.sum(cp_switches_cost(r,l,s)*self.X[(r,l)] for r in self.scenario.requests_dict for l in self.req_cp_locations[r]) <=self.switches_online_capacity[s] )
		#print ("CP switches capacity constraint created")	
		###################################links capacity	
		#for lk in self.links_online_capacity:
		#	if(self.tree.links_dict[lk].level!=LEVEL2):
			#print (lk)
		#		self.cpmodel.add(self.cpmodel.sum(cp_links_cost(r,l,lk)*self.X[(r,l)] for r in self.scenario.requests_dict for l in self.req_cp_locations[r])<=self.links_online_capacity[lk])
	#	print ("CP links capacity constraint created")	
		################ objctive function
		#Obj='S' or 'L' or 'both+' or both_Perc_S or  both_Perc_L
		self.S_Obj=self.cpmodel.sum(self.scenario.requests_dict[r].switches_cost_list[self.cp_locations[l].switches[s]]*self.X[(r,l)] for r in self.scenario.requests_dict for l in self.req_cp_locations[r] for s in self.cp_locations[l].switches)/total_R
		self.L_Obj=self.cpmodel.sum(self.cp_links_weight[lk]*self.scenario.requests_dict[r].link_cost*self.cp_locations[l].links[lk]*self.X[(r,l)] for r in self.scenario.requests_dict for l in self.req_cp_locations[r] for lk in self.cp_locations[l].links)/total_L
		
	def add_location_to_requests(self,location,location_type):
		
		#########Location is cp_location
		#print (location.__dict__)
		s=list(location.switches.keys())[0]
		for (h,m) in self.req_cp_locations:
			if(location.level==LEVEL0):
				if s in self.tree.hosts_list[h].parent_switches[LEVEL0]:
					self.req_cp_locations[(h,m)].append(location.index)
			elif(self.module.modules_list[m].type==location_type):
				if(location.level==LEVEL1):
					if(self.tree.hosts_list[h].pod_index==self.tree.switches_list[s].pod_index):
						self.req_cp_locations[(h,m)].append(location.index)
				if(location.level==LEVEL2):
					self.req_cp_locations[(h,m)].append(location.index)
		add_to_file(self,'a',"\n cp-location["+str(location.index)+"] Level="+str(location.level)
		+"\nswicthes"+str(location.switches)
		+"\nlinks="+str(location.links),self.tree.trace,False)
		#print (self.req_cp_locations)

	def build_level0_locations(self):
		#########Level 0 locations   (one location for each switch)  All class types
		level=LEVEL0
		location_type=STATELESS
		links={}
		routes={}
		for s in Switch.switches_list_in_level[LEVEL0]:
			#index=i
			switches={s:MAIN_INSTANCE_LEVEL0}
			cp_location=CP_Location(self.cp_locations_index,level,switches,links,routes)
			self.cp_locations.append(cp_location)
			self.add_location_to_requests(cp_location,location_type)	
			self.cp_locations_index+=1

	def build_level1_stateless_locations(self):
		#################Level 1 locations 		 (stateless) one location per pod
		level=LEVEL1
		location_type=STATELESS
		links={}
		routes={}
		for pod_index in range(self.tree.no_of_pods):
			pod_switches=find_switches_in_pod_in_level(pod_index,LEVEL1)
			switches={s:MAIN_INSTANCE_LEVEL1 for s in pod_switches}
			cp_location=CP_Location(self.cp_locations_index,level,switches,links,routes)
			self.cp_locations.append(cp_location)
			self.add_location_to_requests(cp_location,location_type)	
			self.cp_locations_index+=1
	
	def build_level2_stateless_locations(self):

		###########Level 2 location (only one)
		level=LEVEL2
		location_type=STATELESS
		links={}
		routes={}
		switches={s:MAIN_INSTANCE_LEVEL2 for s in Switch.switches_list_in_level[LEVEL2]}
		cp_location=CP_Location(self.cp_locations_index,level,switches,links,routes)
		self.cp_locations.append(cp_location)
		self.add_location_to_requests(cp_location,location_type)
		###get ready for next locaation
		self.cp_locations_index+=1

	def build_level_1_stateful_locations_relaxed_version(self):

		level=LEVEL1
		links={}
		links['EXTRA_LINK_LEVEL_11']=0
		routes=[]
		location_type=STATEFUL
		link_share=Switch.no_of_switches_per_pod
		#Get comminucation cost
		switches_list=find_switches_in_pod_in_level(0,level)
		#print (switches_list[0],switches_list[1:])
		comm_routes_dict=self.get_one_route_to_switch(switches_list[0],switches_list[1:])
		
		for route in comm_routes_dict:
			#print (route,comm_routes_dict[route])
			route_links=find_links_for_route(comm_routes_dict[route])
			links['EXTRA_LINK_LEVEL_11']+=link_share*len(route_links)
		
		for switch in Switch.switches_list_in_level[LEVEL1]:
			switches={}
			#pod_switches=find_switches_in_pod_in_level(self.tree.switches_list[s].pod_index,LEVEL1)
			pod_index=self.tree.switches_list[switch].pod_index
			switches_list=find_switches_in_pod_in_level(pod_index,level)
			#print (switch,pod_index,switches_list)
			################Resources cost  swicthes={}
			for s1 in switches_list:
				switches[s1]=MONITORING_INSTANCE_LEVEL1
			switches[switch]=MAIN_INSTANCE_LEVEL1
			#######################comm cost
			cp_location=CP_Location(self.cp_locations_index,level,switches,links,routes)
			self.cp_locations.append(cp_location)
			self.add_location_to_requests(cp_location,location_type)
			###get ready for next locaation
			self.cp_locations_index+=1
		self.cp_links_weight['EXTRA_LINK_LEVEL_11']=Link.parameters["Weight_Links_in_Level_list"][LEVEL1]
			
				
	def build_level_2_stateful_locations_relaxed_version(self):
		
		location_type=STATEFUL
		links={}
		links['EXTRA_LINK_LEVEL_1']=0
		links['EXTRA_LINK_LEVEL_2']=0
		level=LEVEL2
		routes=[]
		#############Calaculate linkshare in level2
		link_share_level_1=0
		link_share_level_2=0
		#link_share=0
		comm_routes_dict=self.get_one_route_to_switch(Switch.switches_list_in_level[LEVEL2][0],Switch.switches_list_in_level[LEVEL2][1:])
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
		
			#link_share+=len(route_links)
		#print (link_share)
		#print (link_share,link_share_level_1,link_share_level_2)
		#if(link_share!=(link_share_level_1+link_share_level_2)):
		#	print ("Error in main cp class share link in realxed version level2")
		#	exit()
		##################################
		#links['EXTRA_LINK']=link_share
		links['EXTRA_LINK_LEVEL_1']=link_share_level_1
		links['EXTRA_LINK_LEVEL_2']=link_share_level_2
		#print (links['EXTRA_LINK_LEVEL_1'],links['EXTRA_LINK_LEVEL_2'])
		#exit()
		switches_list=Switch.switches_list_in_level[LEVEL2]
		for switch in Switch.switches_list_in_level[LEVEL2]:
			switches={}
			new_switches_list=deepcopy(switches_list)
			new_switches_list.remove(switch)
			########################
			################Resources cost  swicthes={}
			for s1 in switches_list:
				switches[s1]=MONITORING_INSTANCE_LEVEL2
			switches[switch]=MAIN_INSTANCE_LEVEL2
			#link_share=1
			#######################comm cost
			cp_location=CP_Location(self.cp_locations_index,level,switches,links,routes)
			#print (cp_location.links)
			self.cp_locations.append(cp_location)
			self.add_location_to_requests(cp_location,location_type)
			###get ready for next locaation
			self.cp_locations_index+=1
		############Fill self.cp_links_weight
		for link in self.tree.links_dict:
			if(self.tree.links_dict[link].level==LEVEL1):
				self.cp_links_weight[link]=self.tree.links_dict[link].weight
		
		#self.cp_links_weight={}
		self.cp_links_weight['EXTRA_LINK_LEVEL_1']=Link.parameters["Weight_Links_in_Level_list"][LEVEL1]
		self.cp_links_weight['EXTRA_LINK_LEVEL_2']=Link.parameters["Weight_Links_in_Level_list"][LEVEL2]
		#print (self.cp_links_weight)
	
	def build_cp_locations(self):

		######reg_location will hold locations indeses
		self.req_cp_locations={(h,m):[] for h in self.scenario.requests_h_m_dict_dict for m in self.scenario.requests_h_m_dict_dict[h]}
		#index=0
		self.build_level0_locations()
		self.build_level1_stateless_locations()
		self.build_level2_stateless_locations()
		#print ("finish stateless")
		self.build_level_1_stateful_locations_relaxed_version()
		#print ("finish stateful1")
		self.build_level_2_stateful_locations_relaxed_version()
		#print ("CP locations Completed")
		
			
			
if __name__ == '__main__':
	
	Fat_tree={"k":6}
	files={"path":"Result/"}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,1]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	
	scenario={"host_modules_request_rate":5,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}

	modules={"max_size_of_module":switches["rack_capacity"]/scenario["host_modules_request_rate"],"stateless_modules_per":0.5,
	"number_of_modules":20,"modules_size_mean_per":0.5,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.3,"comm_cost_stdev_per":0.1}
	
	cp={"timeout":30,"trace_log":True}
	


	#parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	#"over_ratio_weighted_only_over_links","over_ratio_weighted_All_links","over_ratio_only_over_links","over_ratio_All_links","Requested_R_per"]
	
	
	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	algorithm=ALGORITHM_CP_STATELESS_PERC

	A=CP_Main_Allocation(scenario=S,algorithm=algorithm,cp_parameters=cp,switches_online_capacity={},links_online_capacity={})
	
	
	print ("OK")
	#print vars(A)
						
