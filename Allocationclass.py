from Scenarioclass import *
from networkx.algorithms.shortest_paths.generic import all_shortest_paths,shortest_path
import itertools
from collections import Counter
import datetime


##########Allocation
class Allocation(object):

	def __init__(self,scenario,algorithm):
		
		##iniliaize Allocation
		self.algorithm=algorithm
		self.tree=scenario.module.tree
		self.module=scenario.module
		self.scenario=scenario
		self.file=self.tree.files_path+"Allocation.txt"
		self.h_m_allocation_dict_dict={}
		self.start_time=datetime.datetime.now()
		
		
		######Allocation Data structure    this is dictonary of req allocation objects
		###########################={h:{m:req_allocation}}
		self.h_m_allocation_dict_dict={i:{j:UN_ALLOCATED_YET for j in self.scenario.requests_h_m_dict_dict[i]} for i in range(Host.no_of_hosts)}
		
		###########initialise data structure
		self.switches_online_capacity={}
		##########links_online_cpapcity  =online capacity after flow subraction
		self.links_online_capacity={}
		##########################links capacity before a is orignal capacity before subratcting flow
		self.links_capacity_before_A={}
		
		#####Resources Data structure
		self.build_initial_switches_capacity()
		self.build_initial_links_bandwidth()	
		#####Update links Capacity
		self.update_links_online_capacity()
		
		if(algorithm!=ALGORITHM_BFD_SINGLE_INSTANCE):
			self.update_requests_cost()
	
		add_to_file(self,'w',
			"k="+str(self.tree.k)
			#+"\nallocation parameters"+str(scenario_parameters)
			+"\nbefore allocation"
			+"\nswitches_online_capacity\n"+str(self.switches_online_capacity)
			+"\nlinks bandwidth after flow rate\n"+str(self.links_online_capacity),self.tree.trace,False)

		
	def update_requests_cost(self):
		for r in self.scenario.requests_dict:
			(h,m)=r
			valid,req_allocation=self.find_valid_allocation(h,m,LEVEL0)
			if(not valid):
				print ("error in allocating 0")
				exit()
			
			self.scenario.requests_dict[r].total_switches_cost[LEVEL0]=req_allocation.total_comp_cost
			self.scenario.requests_dict[r].total_links_cost[LEVEL0]=req_allocation.total_comm_cost
			
			valid,req_allocation=self.find_valid_allocation(h,m,LEVEL1)
			if(not valid):
				print ("error in allocating 0")
				exit()
			
			self.scenario.requests_dict[r].total_switches_cost[LEVEL1]=req_allocation.total_comp_cost
			self.scenario.requests_dict[r].total_links_cost[LEVEL1]=req_allocation.total_comm_cost
			
			valid,req_allocation=self.find_valid_allocation(h,m,LEVEL2)
			if(not valid):
				print ("error in allocating 0")
				exit()
			
			self.scenario.requests_dict[r].total_switches_cost[LEVEL2]=req_allocation.total_comp_cost
			self.scenario.requests_dict[r].total_links_cost[LEVEL2]=req_allocation.total_comm_cost
			if(self.module.modules_list[m].type==STATEFUL):
				self.scenario.requests_dict[r].total_switches_cost[LEVEL4]=self.scenario.requests_dict[r].total_switches_cost[LEVEL0]*50
			else:
				self.scenario.requests_dict[r].total_switches_cost[LEVEL4]=self.scenario.requests_dict[r].total_switches_cost[LEVEL0]*50

			
	def build_initial_switches_capacity(self):

		for s_index in range(Switch.no_of_switches):
			self.switches_online_capacity[s_index]=self.tree.switches_list[s_index].capacity

	def build_initial_links_bandwidth(self):	

		for (x,y) in self.tree.links_dict:
			self.links_online_capacity[(x,y)]=self.tree.links_dict[(x,y)].bandwidth_with_ovs
			self.links_capacity_before_A[(x,y)]=self.tree.links_dict[(x,y)].bandwidth_with_ovs

	def update_links_online_capacity(self):
		#updates  link.start_switch,link.end_switch]['online_BW'] in tree graph
		for host_index in range(Host.no_of_hosts):
			for route in self.tree.hosts_list[host_index].ECMP_traffic_routes:
				flowsize=self.scenario.get_flow_size_for_host_route(host_index)
				links_list=find_links_for_route(route)
				for link in links_list:
					self.links_online_capacity[link]-=flowsize
					self.links_capacity_before_A[link]-=flowsize
		##Check if any is negative
		for link in self.tree.links_dict.values():
			if self.links_online_capacity[(link.start_switch,link.end_switch)]<0:
				print ("error in main flows capacity<0")
				exit()

	def check_host_flows_and_modules(self):

		for h in self.scenario.requests_h_m_dict_dict:
			sum=0
			##################################
			for route in self.hosts_online_flow_route_dict_dict_tuple[h]:
				if route[-1]!=self.hosts_online_parents_per_level[h][0][0]:###one switch
					print ("Error in checking flows End switch is not TOR"),h,route
					exit()
				sum+=self.hosts_online_flow_route_dict_dict_tuple[h][route]
			if (self.scenario.host_traffic_demand_dict[h]-sum)>len(self.tree.hosts_list[h].parent_switches[2]):
				print ("Error in sum of flows at TOR switch 1"),self.scenario.host_traffic_demand_dict[h],sum,self.tree.hosts_dict[h].parents[2]
			for m in self.scenario.requests_h_m_dict_dict[h]:
				if(self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED):
					#print ()
					continue
				level=self.h_m_allocation_dict_dict[h][m].level
				
				if level>=0:
					sum=0
					for flow in self.hosts_online_flow_route_dict_dict_tuple[h]:
						sum+=self.hosts_online_flow_route_dict_dict_tuple[h][flow]
					if(self.scenario.host_traffic_demand_dict[h]-sum)>len(self.tree.hosts_list[h].parent_switches[2]):
						print ("Error in sum of flows at TOR switch 2"),self.scenario.host_traffic_demand_dict[h],sum,self.tree.hosts_dict[h].parents[2]
						exit()	
	
	def get_all_routes_to_switch(self,switch,new_swithes_list):
			comm_routes={}
			routes=[]
			for s1 in new_swithes_list:
				if(s1==switch):
					continue
				routes=[route for route in all_shortest_paths(self.tree.graph,s1,switch)]
				shuffle(routes)
				comm_routes[s1]=routes[0:]
			return comm_routes
	
	def get_one_route_to_switch(self,switch,new_swithes_list):
			comm_routes={}
			route=0
			for s1 in new_swithes_list:
				if(s1==switch):
					continue
				route=shortest_path(self.tree.graph,s1,switch)
				comm_routes[s1]=route
			return comm_routes
	
	def get_numeric_combination_generator_order_by_new_switch_list(self,comm_routes,switch,switch_list):
		#create numberic mertic to get commbination
		numeric_metric=[]
		for s1 in switch_list:
			if s1==switch:  # to skip main switch
				continue
			routes_index_list=[i for i in range(len(comm_routes[s1]))]
			numeric_metric.append(routes_index_list)

		numeric_metric_combination=itertools.product(*numeric_metric)
		return numeric_metric_combination

	def get_results(self,parameters_list):
		
		for s in self.switches_online_capacity:
			if(self.switches_online_capacity[s]<0):
				print ("error in allocation results switches ")
		for l in self.links_online_capacity:
			if(self.links_online_capacity[l]<0):
				print ("error in allocation results links ")
		#####Modules numbers 
		Total_m=float(0)
		Unallocated_m=float(0)
		Residual_S_R=float(sum(self.switches_online_capacity.values()))
		Residual_L_R=float(0)
		Execuation_time=(datetime.datetime.now()-self.start_time).seconds
		
		
		Unallocated_R=0
		Requested_R=float(0)
		Level_0_allocation=0
		Level_1_allocation=0
		Level_2_allocation=0
		Total_S_R=float(sum([self.tree.switches_list[s_index].capacity for s_index in range(Switch.no_of_switches)]))   #no of switches 5k/4 = (k/2 *k )*2 + (k/2)**2
		Total_L_R=float(sum([self.tree.links_dict[(x,y)].bandwidth for (x,y) in self.tree.links_dict]))

		
		
		Total_L_R_weighted=float(0)
		ecmp_consumed_L_R_weighted=float(0)
		consumed_L_R_weighted=float(0)	
		overhead_consumed_L_R_weighted=float(0)
		
		for link in self.tree.links_dict:
		
			Total_L_R_weighted+=self.tree.links_dict[link].bandwidth*self.tree.links_dict[link].weight
			ecmp_consumed_L_R_weighted+=(self.tree.links_dict[link].bandwidth_with_ovs-self.links_capacity_before_A[link])*self.tree.links_dict[link].weight
			consumed_L_R_weighted+=(self.tree.links_dict[link].bandwidth_with_ovs-self.links_online_capacity[link])*self.tree.links_dict[link].weight
			Residual_L_R+=self.links_online_capacity[link]-self.tree.links_dict[link].bandwidth_with_ovs
		
		overhead_consumed_L_R_weighted=consumed_L_R_weighted-ecmp_consumed_L_R_weighted

		
		################################## unallocted
		#print (self.h_m_allocation_dict_dict)
		Requested_R_stateless=self.scenario.requested_R_stateless
		Requested_R_stateful=self.scenario.requested_R_stateful
		Requested_R=self.scenario.requested_R
		for (h,m) in self.scenario.requests_dict:
			Total_m+=1
			request_comp=self.scenario.requests_dict[(h,m)].switches_cost_list[MAIN_INSTANCE_LEVEL0]
			if self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED:
				Unallocated_R+=request_comp
				if (self.module.modules_list[m].type==STATEFUL):
					Unallocated_m+=1
			elif self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED_YET:
				print ("error in unallocated yet result")
				exit()
			elif self.h_m_allocation_dict_dict[h][m].level==LEVEL0 and self.module.modules_list[m].type==STATEFUL :
				Level_0_allocation+=1
			elif self.h_m_allocation_dict_dict[h][m].level==LEVEL1 and self.module.modules_list[m].type==STATEFUL:
				Level_1_allocation+=1
			elif self.h_m_allocation_dict_dict[h][m].level==LEVEL2 and self.module.modules_list[m].type==STATEFUL:
				Level_2_allocation+=1
			elif self.module.modules_list[m].type==STATELESS:
				x=1
			else: 
				print ("Eror in allocation level results ")
				exit()

		#print (Total_m,Unallocated_m,Unallocated_m/Total_m)			
		if(Unallocated_m>0):
			Success_rate=0
		else:
			Success_rate=1			
		Switches_sumlevel0=0
		Switches_sumlevel1=0
		Switches_sumlevel2=0
		total_switches_sumlevel0=0
		total_switches_sumlevel1=0
		total_switches_sumlevel2=0
		for s in self.switches_online_capacity:
			level=self.tree.switches_list[s].level
			if level==LEVEL0:
				Switches_sumlevel0+=self.switches_online_capacity[s]
				total_switches_sumlevel0+=self.tree.switches_list[s].capacity
			if level==LEVEL1:
				Switches_sumlevel1+=self.switches_online_capacity[s]
				total_switches_sumlevel1+=self.tree.switches_list[s].capacity
			if level==LEVEL2:
				Switches_sumlevel2+=self.switches_online_capacity[s]
				total_switches_sumlevel2+=self.tree.switches_list[s].capacity
				
		parameter_maping={"Total_m":Total_m,
							"Un_allocated_m":Unallocated_m,
							"Allocated_m":Total_m-Unallocated_m,
							"Requested_R":Requested_R,
							"Un_allocated_R":Unallocated_R,
							"Allocated_R":Requested_R-Unallocated_R,
							"Total_S_R":Total_S_R,
							"Total_L_R":Total_L_R,
							"Total_L_R_weighted":Total_L_R_weighted,
							"Residual_S_R":Residual_S_R,
							"Residual_L_R":Residual_L_R,
							"Residual_S_R_per":Residual_S_R/Total_S_R,
							"Residual_L_R_per":Residual_L_R/Total_L_R,
							"Consumed_S_R":Total_S_R-Residual_S_R,
							"Consumed_L_R":Total_L_R-Residual_L_R,
							"Consumed_L_R_weighted":consumed_L_R_weighted,
							"Overhead_consumed_L_R_weighted":overhead_consumed_L_R_weighted,
							"Consumed_S_R_per":((Total_S_R-Residual_S_R)/Total_S_R),
							"Consumed_L_R_per":((Total_L_R-Residual_L_R)/Total_L_R),
							"Consumed_L_R_weighted_per":consumed_L_R_weighted/float(Total_L_R_weighted),
							"Overhead_consumed_L_R_weighted_per over total":overhead_consumed_L_R_weighted/float(Total_L_R_weighted),
							"Overhead_consumed_L_R_weighted_per over consumed":overhead_consumed_L_R_weighted/float(consumed_L_R_weighted),
							"Requested_R_per":(Requested_R/Total_S_R),
							"Un_allocated_m_per":(Unallocated_m/Total_m),
							"allocated_m_per":((Total_m-Unallocated_m)/Total_m),
							"allocated_m_Level_0_per":((Level_0_allocation)/float(Total_m-Unallocated_m)),
							"allocated_m_Level_1_per":((Level_1_allocation)/float(Total_m-Unallocated_m)),
							"allocated_m_Level_2_per":((Level_2_allocation)/float(Total_m-Unallocated_m)),
							"Residual_S_level0":((Switches_sumlevel0)/float(total_switches_sumlevel0)),
							"Residual_S_level1":((Switches_sumlevel1)/float(total_switches_sumlevel1)),
							"Residual_S_level2":((Switches_sumlevel2)/float(total_switches_sumlevel2)),
							"Requested_R_0":Requested_R_stateless/float(Requested_R),
							"Requested_R_1":Requested_R_stateful/float(Requested_R),
							"Execution_time":Execuation_time,
							"Success_rate":Success_rate,
							"Allocated_R_per":(Requested_R-Unallocated_R)/float(Requested_R),
							}
		return [parameter_maping[parameter] for parameter in parameters_list]



	def check_valid_allocation(self,h,m,req_allocation):
		
		#########switches cost
		for switch_index in req_allocation.switches_cost_dict:
			if (self.switches_online_capacity[switch_index]-req_allocation.switches_cost_dict[switch_index])<0:
				self.print_req_allocation(h,m,req_allocation,False)
				add_to_file(self,'a',"\n Unvalid Switches Capacity",self.tree.trace,False)
				return (False,NOT_ENOUGHT_COMP)
		################links cost
		links_dict={}
		for (route,cost) in req_allocation.links_cost_list:
			links_list=find_links_for_route(route)
			for link in links_list:
				if(link in links_dict):
					links_dict[link]+=cost
				else:
					links_dict[link]=cost
			
		for link in links_dict:####link=(1,5)
			cost=links_dict[link]
			if (self.links_online_capacity[link]-cost)<0:
				self.print_req_allocation(h,m,req_allocation,False)
				add_to_file(self,"a","\n Unvalid Links Capacity",self.tree.trace,False)
				return (False,NOT_ENOUGHT_BW)
		################flow replacment cost
		old_links_dict={}
		new_links_dict={}
		if(req_allocation.flows_replacement and self.algorithm!=ALGORITHM_BFD_SINGLE_INSTANCE):
			print ("error in flow replacment ")
			exit()
		if(req_allocation.links_cost_list and req_allocation.flows_replacement ):
			print ("errrrror in allocaion check valid links cost and  flows_replacement  ")
			exit()
		for (oldpath,newpath,size) in req_allocation.flows_replacement:
			##############path is tuple of switches
			old_links=find_links_for_route(oldpath)
			new_links=find_links_for_route(newpath)
			for link in old_links:
				if(link in old_links_dict):
					old_links_dict[link]+=size
				else:
					old_links_dict[link]=size
			for link in new_links:
				if(link in new_links_dict):
					new_links_dict[link]+=size
				else:
					new_links_dict[link]=size
				
		for link in new_links_dict:
			if(link in old_links_dict):
				if((self.links_online_capacity[link]+old_links_dict[link]-new_links_dict[link])<0):
					self.print_req_allocation(h,m,req_allocation,False)
					add_to_file(self,"a","\n Unvalid Links Capacity for new route",self.tree.trace,False)
					return (False,NOT_ENOUGHT_BW)
			else:
				if((self.links_online_capacity[link]-new_links_dict[link])<0):
					self.print_req_allocation(h,m,req_allocation,False)
					add_to_file(self,"a","\n Unvalid Links Capacity for new route",self.tree.trace,False)
					return (False,NOT_ENOUGHT_BW)
		return True,ENOUGHT

	def update_allocation(self,h,m,req_allocation):
		self.h_m_allocation_dict_dict[h][m]=req_allocation
		self.print_req_allocation(h,m,req_allocation,True)
		add_to_file(self,'a',"\n Update",self.tree.trace,False)
		if(req_allocation==UN_ALLOCATED):
			return True
		
		#############Switches cost
		for switch_index in req_allocation.switches_cost_dict:
			add_to_file(self,"a","\n switch update:s"+str(switch_index)+"="+str(self.switches_online_capacity[switch_index]),self.tree.trace,False)
			self.switches_online_capacity[switch_index]-=req_allocation.switches_cost_dict[switch_index]
			add_to_file(self,"a"," --> "+str(self.switches_online_capacity[switch_index]),self.tree.trace,False)
			if (self.switches_online_capacity[switch_index]<0):
				print (self.switches_online_capacity[switch_index])
				print ("ERROR in update switches")
				exit()
		###############links cost
		if(req_allocation.links_cost_list and (self.module.modules_list[m].type==STATELESS)):
			print ("Error in updae allocation links to statless module")
			exit()
		for (route,cost) in req_allocation.links_cost_list:
			links_list=find_links_for_route(route)
			for link in links_list:####link=(1,5)
				add_to_file(self,"a","\n link update:s"+str(link)+"="+str(self.links_online_capacity[link]),self.tree.trace,False)
				self.links_online_capacity[link]-=cost
				add_to_file(self,"a"," --> "+str(self.links_online_capacity[link]),self.tree.trace,False)
				if (self.links_online_capacity[link]<0):
					print (self.links_online_capacity[link])
					print ("ERROR in update links")
					exit()
		
		###Flow replcement cost
		if len(req_allocation.flows_replacement)>0:
			add_to_file(self,"a","\n Flow replacement ",self.tree.trace,False)
		for (oldpath,newpath,size) in req_allocation.flows_replacement:
			add_to_file(self,"a","\n"+str(oldpath)+" --> "+str(newpath),self.tree.trace,False)
			##############path is tuple of switches
			old_links=find_links_for_route(oldpath)
			new_links=find_links_for_route(newpath)
			
			for link in old_links:
				add_to_file(self,"a","\n link update:s"+str(link)+"="+str(self.links_online_capacity[link]),self.tree.trace,False)
				self.links_online_capacity[link]+=size
				add_to_file(self,"a"," --> "+str(self.links_online_capacity[link]),self.tree.trace,False)

			for link in new_links:
				add_to_file(self,"a","\n link update:s"+str(link)+"="+str(self.links_online_capacity[link]),self.tree.trace,False)
				self.links_online_capacity[link]-=size
				if (self.links_online_capacity[link]<-1):
					print (self.links_online_capacity[link])
					print ("ERROR in update links flow replacment")
					exit()
				
				add_to_file(self,"a"," --> "+str(self.links_online_capacity[link]),self.tree.trace,False)
			
			
			del self.hosts_online_flow_route_dict_dict_tuple[h][oldpath]
			self.hosts_online_flow_route_dict_dict_tuple[h][newpath]=size
		#################Parent cost
		for (L,s) in req_allocation.parent_replacement:
			self.hosts_online_parents_per_level[h][L]=[s]
		if len(req_allocation.parent_replacement)>0:
			add_to_file(self,"a","\n parent update \n"+str(self.hosts_online_parents_per_level[h]),self.tree.trace,False)
		
		return True
	
	
	###########This function is not valid for single _instance
	########
	def unallocate_req(self,h,m):
		
		################Convert request to unallocated yet 
		###############Used In TABU and nearoptimal
		req_allocation=deepcopy(self.h_m_allocation_dict_dict[h][m])
		if(req_allocation in [UN_ALLOCATED_YET,UN_ALLOCATED] and (self.algorithm in TABU_RANDOM_ALGORITHMS_LIST+TABU_BFD_ALGORITHMS_LIST)):
			self.h_m_allocation_dict_dict[h][m]=UN_ALLOCATED_YET
			return
		if len(req_allocation.flows_replacement)>0:
			print ("error in unallocate req")
			exit()
		
		self.h_m_allocation_dict_dict[h][m]=UN_ALLOCATED_YET
		#############Switches cost
		for switch_index in req_allocation.switches_cost_dict:
			self.switches_online_capacity[switch_index]+=req_allocation.switches_cost_dict[switch_index]
			
		###############links cost
		for (route,cost) in req_allocation.links_cost_list:
			links_list=find_links_for_route(route)
			for link in links_list:####link=(1,5)
				self.links_online_capacity[link]+=cost

	def print_req_allocation(self,h,m,req_allocation,valid):

		if(req_allocation==UN_ALLOCATED or req_allocation==UN_ALLOCATED_YET):
			add_to_file(self,"a","\n "+str(h)+" "+str(m)+" level="+str(req_allocation)+" type="+str(self.module.modules_list[m].type),self.tree.trace,False)
			return
		add_to_file(self,"a","\n "+str(h)+" "+str(m)+" level="+str(req_allocation.level)+" type="+str(self.module.modules_list[m].type),self.tree.trace,False)
		add_to_file(self,"a","\n baseline_cost="+str(self.scenario.requests_h_m_dict_dict[h][m].baseline_cost),self.tree.trace,False)
		add_to_file(self,"a","\n traffic_cost="+str(self.scenario.requests_h_m_dict_dict[h][m].traffic_cost),self.tree.trace,False)	
		add_to_file(self,"a","\n comm_cost="+str(self.scenario.requests_h_m_dict_dict[h][m].comm_cost),self.tree.trace,False)
		add_to_file(self,"a","\n allocation_comp_cost="+str(req_allocation.switches_cost_dict),self.tree.trace,False)
		add_to_file(self,"a","\n allocation_comm_cost="+str(req_allocation.links_cost_list),self.tree.trace,False)
		if self.algorithm==ALGORITHM_BFD_SINGLE_INSTANCE:
			add_to_file(self,"a","\n flow_replacements="+str(req_allocation.flows_replacement),self.tree.trace,False)
			add_to_file(self,"a","\n parent_replacement="+str(req_allocation.parent_replacement),self.tree.trace,False)
			add_to_file(self,"a","\n online parent for h="+str(self.hosts_online_parents_per_level[h]),self.tree.trace,False)
			add_to_file(self,"a","\n online flow routes for h="+str(self.hosts_online_flow_route_dict_dict_tuple[h]),self.tree.trace,False)

		add_to_file(self,"a","\n allocation valid="+str(valid),self.tree.trace,False)

	def get_unallocated_yet_requests(self):
		unalllocated_request_list=[]
		for (h,m) in self.scenario.requests_dict:
			if(self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED_YET):
				unalllocated_request_list.append((h,m))

		return unalllocated_request_list
	
	def get_all_unallocated_requests(self):
		unalllocated_request_list=[]
		for (h,m) in self.scenario.requests_dict:
			if(self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED_YET or self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED ):
				unalllocated_request_list.append((h,m))

		return unalllocated_request_list
	
	def get_new_comm_link(self,basic_comm_routes_dict,comm_cost_per_link):
	
		new_comm_routes_dict=deepcopy(basic_comm_routes_dict)
		for route_switch in basic_comm_routes_dict:
			for route in basic_comm_routes_dict[route_switch]:
				route_links=find_links_for_route(route)
				for route_link in route_links:
					if((self.links_online_capacity[route_link]-comm_cost_per_link)<0):
						new_comm_routes_dict[route_switch].remove(route)
						break
		
			if(not new_comm_routes_dict[route_switch]):
				return False,0
		
		return True,new_comm_routes_dict
	
	#########Update to make fit both 
	#
	def create_req_allocation_for_cp_location(self,h,m,cp_location):

		route_link_cost=0
		if(cp_location.level==LEVEL1):
			route_link_cost=self.scenario.requests_dict[(h,m)].link_cost*Switch.no_of_switches_per_pod
		if(cp_location.level==LEVEL2):
			route_link_cost=self.scenario.requests_dict[(h,m)].link_cost
		
		allocation_comp_cost={}
		allocation_comm_cost=[]
		for s in cp_location.switches:
			switch_cost_type=cp_location.switches[s]
			allocation_comp_cost[s]=self.scenario.requests_dict[(h,m)].switches_cost_list[switch_cost_type]
		for route in cp_location.routes:
			allocation_comm_cost.append((route,route_link_cost))
		
		req_allocation=Request_Allocation(cp_location.level,allocation_comp_cost,allocation_comm_cost)

		return req_allocation

	
	def get_complete_valid_location_for_level_1_2_after_cp(self,h,m,cp_location):
		
		if(self.algorithm==ALGORITHM_NEAR_OPTIMAL and cp_location.level==LEVEL1):
			print ("Error in allocation GET COMPLETE location in near optimal case")
			exit()
		copy_location=deepcopy(cp_location)
		###################find main switch and monitoring switches in the location
		switch=[]
		new_switches_list=[]
		for s in cp_location.switches:
			if(cp_location.switches[s] in [MAIN_INSTANCE_LEVEL1,MAIN_INSTANCE_LEVEL2] ):
				switch=s
			elif(cp_location.switches[s] in [MONITORING_INSTANCE_LEVEL1,MONITORING_INSTANCE_LEVEL2] ):
				new_switches_list.append(s)
			else:
				print ("Error in get_complete_valid_location in instance type")
				exit()
		
		if(cp_location.level==LEVEL1):
			comm_cost_per_link=self.scenario.requests_h_m_dict_dict[h][m].link_cost*Switch.no_of_switches_per_pod
		if(cp_location.level==LEVEL2):
			comm_cost_per_link=self.scenario.requests_h_m_dict_dict[h][m].link_cost
			

		############complete the location by finding valid valid routes
		#comm routes dict ={ s1:[[],[],[]],s2:[]}
		basic_comm_routes_dict=self.get_all_routes_to_switch(switch,new_switches_list)
		#clean comm_routes_dict from not enough reoutes before start fining combination
		comm_route_valid,new_comm_routes_dict=self.get_new_comm_link(basic_comm_routes_dict,comm_cost_per_link)

		if(not comm_route_valid):
			print ("Error no valid route for level2 allocation cp in comm_routes clean")
			exit()
		
		############create combination for all routes
		numeric_mertic_combination=self.get_numeric_combination_generator_order_by_new_switch_list(new_comm_routes_dict,switch,new_switches_list)
				
		##get links allocation and communication cost
		for combination in numeric_mertic_combination:
			routes=[]
			for j,perm in enumerate(combination):
				route=new_comm_routes_dict[new_switches_list[j]][perm]
				routes.append(route)
			copy_location.routes=routes
			#####################next function Only consider switches and routes of copy_location
			req_allocation=self.create_req_allocation_for_cp_location(h,m,copy_location)
			valid,not_enought=self.check_valid_allocation(h,m,req_allocation)	
			if valid:
				break
		if valid==False:
			print ("Error no valid route for level 1 or 2 allocation cp")
			exit()
		return req_allocation

	def find_valid_allocation(self,h,m,level):
		
		if(self.module.modules_list[m].type==STATELESS):
			valid,req_allocation=self.find_allocation_for_stateless(h,m,level)
			
		elif (self.module.modules_list[m].type==STATEFUL):
			valid,req_allocation=self.find_allocation_for_stateful(h,m,level)
		else:
			print ("Error in type in find valid allocation")
			exit()
		#print ("after find",req_allocation.level)
		return valid,req_allocation
	
	def find_allocation_for_stateless(self,h,m,level):
		###computing_cost={'s':50,'s2':56,....}
		#req_baseline_cost=self.scenario.requests_h_m_dict_dict[h][m].baseline_cost
		#req_traffic_cost=self.scenario.requests_h_m_dict_dict[h][m].traffic_cost
		if(level==LEVEL0):
			main=MAIN_INSTANCE_LEVEL0
		elif(level==LEVEL1):
			main=MAIN_INSTANCE_LEVEL1
		elif(level==LEVEL2):
			main=MAIN_INSTANCE_LEVEL2
		allocation_comp_cost={}
		####return list of switches with computing cost
		switches_list=self.tree.hosts_list[h].parent_switches[level]
		no_of_switches=len(switches_list)
		for switch in switches_list:
			allocation_comp_cost[switch]=self.scenario.requests_h_m_dict_dict[h][m].switches_cost_list[main]

		##############
		req_allocation=Request_Allocation(level,allocation_comp_cost,{})
		valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
		return valid,req_allocation

	
	def find_allocation_for_stateful(self,h,m,level):
		
		#print (level)
		###computing_cost={'s':50,'s2':56,....}
		####return list of switches with computing cost
		#req_baseline_cost=self.scenario.requests_h_m_dict_dict[h][m].baseline_cost
		#req_traffic_cost=self.scenario.requests_h_m_dict_dict[h][m].traffic_cost
		#req_comm_cost=self.scenario.requests_h_m_dict_dict[h][m].comm_cost
		allocation_comp_cost={}
		allocation_comm_cost={}
		req_allocation=0
		valid=False
		#print (h,m,level)
		switches_list=self.tree.hosts_list[h].parent_switches[level]
		no_of_switches=len(switches_list)
		if(level==LEVEL0):
			allocation_comp_cost={self.tree.hosts_list[h].TOR_switch_index:self.scenario.requests_h_m_dict_dict[h][m].switches_cost_list[MAIN_INSTANCE_LEVEL0]}
			req_allocation=Request_Allocation(level,allocation_comp_cost,allocation_comm_cost)
			valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
			return valid,req_allocation
		####level 1 and 2
		else:
			if (level==LEVEL1):
				comm_cost_per_link=self.scenario.requests_h_m_dict_dict[h][m].link_cost*Switch.no_of_switches_per_pod
				#LINK_BW_LEVEL1
				main=MAIN_INSTANCE_LEVEL1
				monitoring=MONITORING_INSTANCE_LEVEL1
			else:
				comm_cost_per_link=self.scenario.requests_h_m_dict_dict[h][m].link_cost
				#link_BW=LINK_BW_LEVEL2
				main=MAIN_INSTANCE_LEVEL2
				monitoring=MONITORING_INSTANCE_LEVEL2
			
			
			switches_list=sorted(switches_list, key=self.switches_online_capacity.get,reverse=True)
			
			for switch in switches_list:
				new_switches_list=deepcopy(switches_list)
				new_switches_list.remove(switch)
				shuffle(new_switches_list)
				
				#######Calculate switches allocation & computing cost for each switch
				allocation_comp_cost={s:self.scenario.requests_h_m_dict_dict[h][m].switches_cost_list[monitoring] for s in new_switches_list}
				allocation_comp_cost[switch]=self.scenario.requests_h_m_dict_dict[h][m].switches_cost_list[main]
				#######Calculate links allocation & communication cost for each link
				###claculate all routes to switch (main switch)
				###comm routes dict ={ s1:[[],[],[]],s2:[]}
				
				basic_comm_routes_dict=self.get_all_routes_to_switch(switch,new_switches_list)
				#clean comm_routes_dict from not enough reroutes before start fining combination
				comm_route_valid,new_comm_routes_dict=self.get_new_comm_link(basic_comm_routes_dict,comm_cost_per_link)		
				if(not comm_route_valid):
					continue
				
				############create combination for all routes
				numeric_mertic_combination=self.get_numeric_combination_generator_order_by_new_switch_list(new_comm_routes_dict,switch,new_switches_list)
				
				##get links allocation and communication cost
				for combination in numeric_mertic_combination:
					#print ("new combination",combination)	
					####allocation_comm_cost= [([15,7,14],3.2),(),(),()] all cost equal
					allocation_comm_cost=[]
					for j,perm in enumerate(combination):
						allocation_comm_cost.append((new_comm_routes_dict[new_switches_list[j]][perm],comm_cost_per_link))
					req_allocation=Request_Allocation(level,allocation_comp_cost,allocation_comm_cost)
					valid,not_enought=self.check_valid_allocation(h,m,req_allocation)
					if valid:
						return valid,req_allocation

					#####Following if to break if switches capacity is not enough without going on all links combination
					if not_enought==NOT_ENOUGHT_COMP:
						break	
		############This return for not valid 
		return valid,req_allocation
	def sort_requests(self):
		#Algorithms  BFD,FFD,BFD_SINGLE_INSTANCE,BFD_COMP_PLUS_COMM,BFD_comm,BFD_STATELESS,BFD_STATEFUL,BFA_COMP,BF,RANDOM
		##Request orders  COMP_DEC,COMM_DEC,BFD_SINGLE_INSTANCE,COMP_DEC_STATELESS_FIRST,COMP_DEC_STATEFUL_FIRST
					###COMP_PLUS_COMM, COMP_ASC,RANDOM
			
		##ALGORITHM_BFD                ---> ORDERED_BY_COMP_DEC
		##ALGORITHM_FFD                ---> ORDERED_BY_COMP_DEC
		##ALGORITHM_BFD_SINGLE_INSTANCE---> ORDERED_BY_COMP_DEC

		##ALGORITHM_BFD_COMP_PLUS_COMM ---> ORDERED_BY_COMP_PLUS_COMM
		##ALGORITHM_BFD_comm	       ---> ORDERED_BY_COMM_DEC
			
		##ALGORITHM_BFD_STATELESS      ---> ORDERED_BY_COMP_DEC_STATELESS_FIRST
		##ALGORITHM_BFD_STATEFUL       ---> ORDERED_BY_COMP_DEC_STATEFUL_FIRST
		
		##ALGORITHM_BFA_COMP           ---> ORDERED_BY_COMP_ASC
			
		##ALGORITHM_BF                 ---> ORDERED_BY_RANDOM
		##ALGORITHM_FF             	   ---> ORDERED_BY_RANDOM
		##ALGORITHM_RANDOM             ---> ORDERED_BY_RANDOM
		
		#####Sort Requests list
		request_list=[]
		if (self.algorithm==ALGORITHM_BFD or self.algorithm==ALGORITHM_FFD or self.algorithm==ALGORITHM_BFD_SINGLE_INSTANCE):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMP_DEC,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_BFD_comm):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMM_DEC,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_BFD_COMP_PLUS_COMM):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMP_PLUS_COMM,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_BFD_STATELESS):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMP_DEC_STATELESS_FIRST,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_BFD_STATEFUL):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMP_DEC_STATEFUL_FIRST,self.scenario.requests_dict)
		elif self.algorithm==ALGORITHM_BFA_COMP:
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMP_ASC,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_RANDOM or self.algorithm==ALGORITHM_BF or self.algorithm==ALGORITHM_FF):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_RANDOM,self.scenario.requests_dict)
		elif (self.algorithm in TABU_RANDOM_ALGORITHMS_LIST+TABU_BFD_ALGORITHMS_LIST):
			order=ORDERED_BY_COMP_DEC
			request_list=self.scenario.sort_requests_by_order(order,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_LP_BFD or self.algorithm==ALGORITHM_LP_FFD):
			request_list=self.scenario.sort_requests_by_order(ORDERED_BY_COMP_DEC_STATEFUL_FIRST,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_LP_RANDOM):
			order=ORDERED_BY_RANDOM
			request_list=self.scenario.sort_requests_by_order(order,self.scenario.requests_dict)
		elif (self.algorithm==ALGORITHM_LP_BF):
			order=ORDERED_BY_RANDOM_STATEFUL_FIRST
			request_list=self.scenario.sort_requests_by_order(order,self.scenario.requests_dict)
		else:
			print ("Error in algorithms in sort requests allocation class")
			exit()

		return request_list
	
if __name__ == '__main__':
	
	files={"path":"Result/"}
	Fat_tree={"k":4}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.7,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	modules={"max_size_of_module":switches["rack_capacity"],"stateless_modules_per":0.5,
	"number_of_modules":6,"modules_size_mean_per":0.6,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.5,"comm_cost_stdev_per":0.1}

	scenario={"host_modules_request_rate":1,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}
	
	parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	"over_ratio_weighted_only_over_links","over_ratio_weighted_All_links","over_ratio_only_over_links","over_ratio_All_links","Requested_R_per"]

	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	CP_parameters={"Timeout":30}
	
	algorithm=ALGORITHM_BFD
	A=Allocation(scenario=S,algorithm=algorithm)
	
	print ([(x, A.scenario.requests_dict[x].total_switches_cost, A.scenario.requests_dict[x].total_links_cost) for x in A.scenario.requests_dict])
	
	#print (A.switches_online_capacity.values())
	#print ("OK")
	#print vars(A)
