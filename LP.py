from Allocationclass import *
from docplex.mp.model import Model

class LP_Allocation(Allocation):
	
	def __init__(self,scenario,algorithm):
		
		super(LP_Allocation, self).__init__(scenario,algorithm)
		####################################################requestes scenario Data structure(modules)
		self.timeout=1000
		self.trace_log=False
		self.workers=2
		self.msol={}
		
		self.lp_locations=[]
		self.lp_locations_index=0
		self.req_lp_locations={}
		#print ("locations created1")
		self.build_lp_locations()
		#print ("locations created2")
		self.build_lp_main_model()
		
		add_to_file(self,'a',"\nStart allocation process for "+str(ALGORITHMS_NAMES[self.algorithm]),self.tree.trace,False)
		self.lpmodel.minimize(self.S_Obj)
		self.msol = self.lpmodel.solve()
		self.update_allocation_after_solving_lp(self.X,self.msol,self.lp_locations)
		add_to_file(self,'a',"\nAllocation for "+str(ALGORITHMS_NAMES[self.algorithm])+" Completed",self.tree.trace,False)

	def update_allocation_after_solving_lp(self,X,solution,locations_list):
		##########this function will update self allocation with result from x and soution
		############find req_allocation for each x(h,m)=1
		########by creating  rwq_allocation for each location with x(h,m)=1
		#print (45,len(self.lp_locations))
		if(solution):
			# hase update results
			for r,location_index in X:
				(h,m)=r
				lp_location=locations_list[location_index]

				if solution[X[(r,location_index)]]==1:
					if (lp_location.level==LEVEL4):
						print ("\n No valid Allocation found",r)
						self.h_m_allocation_dict_dict[h][m]=UN_ALLOCATED
					else:
						valid,req_allocation=self.find_valid_allocation(h,m,lp_location.level)
						if(valid):
							self.update_allocation(h,m,req_allocation)
						else:
							print (self.switches_online_capacity)
							print ([x for x in self.scenario.requests_dict])
							print (self.algorithm)
							for x in self.lp_locations:
								print (x.switches_dict,x.capacity)
							print ("Error in LP can't find valid allocation")
							exit()
					
		else:
			print (self.switches_online_capacity)
			print ([x for x in self.scenario.requests_dict])
			print (self.algorithm)
			for x in self.lp_locations:
				print (x.switches)
			print (self.req_lp_locations)
			print ("Coudn't reach solution in update after solving LP", self.algorithm)
			exit()
	
	def build_lp_main_model(self):
		
		total_R=sum(self.switches_online_capacity.values())
		total_L=sum(self.links_online_capacity.values())
		
		######### Create CPO model
		self.lpmodel = Model()
	#	print ("CP model created")
		###requests represented by requests_dict={(h,m):obj,(h,m).....}
		##locations are prepsnted by index through self.req_cp_locations[(h,m)]
		self.X=self.lpmodel.binary_var_dict([(r, l) for r in (self.scenario.requests_dict) for l in self.req_lp_locations[r]], name="X")
	#	print ("CP variable created")		
		##################################sum equal 1 constraints   ### single instnace and must have allocation
		for r in self.scenario.requests_dict:
			self.lpmodel.add(self.lpmodel.sum(self.X[(r,l)] for l in self.req_lp_locations[r])==1)
		for l in range(len(self.lp_locations[0:-1])):
			self.lpmodel.add(self.lpmodel.sum(self.scenario.requests_dict[r].total_switches_cost[self.lp_locations[l].level]*self.X[(r,l)] for r in self.scenario.requests_dict if l in self.req_lp_locations[r]) <=self.lp_locations[l].capacity)
#		print ("CP switches capacity constraint created")	
		###################################links capacity	
		################ objctive function
		#Obj='S' or 'L' or 'both+' or both_Perc_S or  both_Perc_L
		self.S_Obj=self.lpmodel.sum(self.scenario.requests_dict[r].total_switches_cost[self.lp_locations[l].level]*self.X[(r,l)] for r in self.scenario.requests_dict for l in self.req_lp_locations[r])
		#print ("CP objectives created")	
		
	
	def build_lp_locations(self):

		######reg_location will hold locations indeses
		self.req_lp_locations={(h,m):[] for h in self.scenario.requests_h_m_dict_dict for m in self.scenario.requests_h_m_dict_dict[h]}
		self.build_level0_locations()
		
		self.build_level1_stateless_locations()
		self.build_level2_stateless_locations()
		self.add_extra_location()
		
	def add_extra_location(self):
		level=LEVEL4
		location_type=STATELESS
		switches_dict=None
		capacity=None
		lp_location=LP_Location(self.lp_locations_index,level,capacity,switches_dict)
		self.lp_locations.append(lp_location)
		self.add_lp_location_to_requests(lp_location,location_type)
		self.lp_locations_index+=1
	
	def build_level0_locations(self):
		#update_requests_cost
		#########Level 0 locations   (one location for each switch)  All class types
		level=LEVEL0
		location_type=STATELESS
		for s in Switch.switches_list_in_level[LEVEL0]:
			switches_dict={s:MAIN_INSTANCE_LEVEL0}
			capacity=self.switches_online_capacity[s]
			lp_location=LP_Location(self.lp_locations_index,level,capacity,switches_dict)
			self.lp_locations.append(lp_location)
			self.add_lp_location_to_requests(lp_location,location_type)	
			self.lp_locations_index+=1
	def build_level1_stateless_locations(self):
		#################Level 1 locations 		 (stateless) one location per pod
		level=LEVEL1
		location_type=STATELESS
		for pod_index in range(self.tree.no_of_pods):
			capacity=0
			pod_switches=find_switches_in_pod_in_level(pod_index,LEVEL1)
			switches_dict={s:MAIN_INSTANCE_LEVEL1 for s in pod_switches}
			for s in switches_dict:
				capacity+=self.switches_online_capacity[s]
			lp_location=LP_Location(self.lp_locations_index,level,capacity,switches_dict)
			self.lp_locations.append(lp_location)
			self.add_lp_location_to_requests(lp_location,location_type)	
			self.lp_locations_index+=1
	
	def build_level2_stateless_locations(self):
		###########Level 2 location (only one)
		level=LEVEL2
		location_type=STATELESS
		switches_dict={s:MAIN_INSTANCE_LEVEL2 for s in Switch.switches_list_in_level[LEVEL2]}
		capacity=0
		for s in switches_dict:
			capacity+=self.switches_online_capacity[s]
		lp_location=LP_Location(self.lp_locations_index,level,capacity,switches_dict)
		self.lp_locations.append(lp_location)
		self.add_lp_location_to_requests(lp_location,location_type)
		###get ready for next locaation
		self.lp_locations_index+=1
	
	def add_lp_location_to_requests(self,location,location_type):
		
		#########Location is cp_location
		if(location.level!=LEVEL4):
			s=list(location.switches_dict.keys())[0]
		for (h,m) in self.req_lp_locations:
			if(location.level==LEVEL0):
				if s in self.tree.hosts_list[h].parent_switches[LEVEL0]:
					self.req_lp_locations[(h,m)].append(location.index)
			elif(location.level==LEVEL4):
				self.req_lp_locations[(h,m)].append(location.index)
			elif(self.module.modules_list[m].type==location_type):
				if(location.level==LEVEL1):
					if(self.tree.hosts_list[h].pod_index==self.tree.switches_list[s].pod_index):
						self.req_lp_locations[(h,m)].append(location.index)
				if(location.level==LEVEL2):
					self.req_lp_locations[(h,m)].append(location.index)
			
		
		add_to_file(self,'a',"\n lp-location["+str(location.index)+"] Level="+str(location.level)
		+"\nswicthes"+str(location.switches_dict)
		+"\nlinks="+str(location.capacity),self.tree.trace,False)
	
if __name__ == '__main__':
	
	Fat_tree={"k":6}
	#####writing_mode='w' or 'a'====> w mean erase old files while 'a' mean extend  already exist files
	files={"path":"Result/"}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	
	scenario={"host_modules_request_rate":5,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}

	modules={"max_size_of_module":switches["rack_capacity"]/scenario["host_modules_request_rate"],"stateless_modules_per":0.5,
	"number_of_modules":20,"modules_size_mean_per":0.5,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.3,"comm_cost_stdev_per":0.1}
	
	cp={"timeout":30,"trace_log":True}

	scenario={"host_modules_request_rate":1,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
	
	
	cp={"timeout":30,"trace_log":True,"workers":4}

	parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	"Requested_R_per"]
	
	
	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	#algorithm=ALGORITHM_CP_COMP
	algorithm=ALGORITHM_LP
	# ALGORITHM_CP_COMM , ALGORITHM_CP_COMP_PLUS_COMM , ALGORITHM_CP_STATEFUL_PERC
	A=LP_Allocation(scenario=S,algorithm=algorithm)
	
	print ("OK")
	#print vars(A)
						
