#from Fattreeclass import *
from ModulesPoolclass import *
from copy import copy,deepcopy

class Scenario(object):
	
	def __init__(self,module,scenario_parameters,scenario_object,class_type):
	
		##########scenario,class_type  paramters is used to build requests from old scenario but with single type
		self.module=module
		self.tree=module.tree
		self.file=self.tree.files_path+"Scenario.txt"
		self.requested_R=0
		self.requested_R_stateless=0
		self.requested_R_stateful=0
		
		self.host_modules_request_rate=scenario_parameters["host_modules_request_rate"]
		self.modules_baseline_per=scenario_parameters["modules_baseline_per"]
		self.flow_distribuation=scenario_parameters["flow_distribuation"]
		###########Build Flow scenario
		self.host_traffic_demand_dict=self.build_hosts_flow_demand()
		###########Build requests
		self.requests_dict={}
		if(scenario_object):
			self.requests_h_m_dict_dict=self.build_requests_for_single_clss_type(scenario_object,class_type)
		else: 
			self.requests_h_m_dict_dict=self.build_requests()
		#############################
		
		add_to_file(self,'w',
			"k="+str(self.tree.k)
			+"\nScenario parameters"+str(scenario_parameters)
			+"\nHosts traffic demand"+str(self.host_traffic_demand_dict)
			+"\nlinks attributes after update flow rate"+json.dumps(list(self.tree.graph.edges.items()), indent = 2)
			+"\nHosts modules requests"+str(self.requests_h_m_dict_dict),self.tree.trace,False)
		#print ("==========>Requests Created")
	
	def get_computing_cost(self,h,m):
		######### return computing baseline cost=m.size*basline_per
		########return  computing traffic cost=m.size*(1-baseline_per)*(h.traffic/max_traffic_rate])
		computing_baseline_cost=self.module.modules_list[m].size*self.modules_baseline_per
		computing_traffic_cost=self.module.modules_list[m].size*(1-self.modules_baseline_per)*(self.host_traffic_demand_dict[h]/Host.max_traffic_rate)
		switches_cost_list=[0.0 for i in range(5)]
		switches_cost_list[MAIN_INSTANCE_LEVEL0]=computing_baseline_cost+computing_traffic_cost
		if(self.module.modules_list[m].type==STATELESS):
			switches_cost_list[MAIN_INSTANCE_LEVEL1]=computing_baseline_cost+computing_traffic_cost/Switch.no_of_switches_per_pod
			switches_cost_list[MAIN_INSTANCE_LEVEL2]=computing_baseline_cost+computing_traffic_cost/Switch.no_level_2_switches
			switches_cost_list[MONITORING_INSTANCE_LEVEL1]=None
			switches_cost_list[MONITORING_INSTANCE_LEVEL2]=None
		elif(self.module.modules_list[m].type==STATEFUL):
			switches_cost_list[MAIN_INSTANCE_LEVEL1]=computing_baseline_cost+computing_traffic_cost
			switches_cost_list[MAIN_INSTANCE_LEVEL2]=computing_baseline_cost+computing_traffic_cost
			switches_cost_list[MONITORING_INSTANCE_LEVEL1]=computing_traffic_cost/Switch.no_of_switches_per_pod
			switches_cost_list[MONITORING_INSTANCE_LEVEL2]=computing_traffic_cost/Switch.no_level_2_switches
		else:
			print ("Error in scenario get_computing_cost")
			exit()
		for n in switches_cost_list:
			if(n==0):
				print ("unvalid switch cost=0 in scenario ")
				exit()
		#switches_cost_list[UNALLOCATED_COST]=100


		return (computing_baseline_cost,computing_traffic_cost,switches_cost_list)

	def get_communication_and_link_cost(self,h,m):
		#return communication cost per of totoal traffic rate of the host
		###return comm_cot=m.comm_cost_per*h.traffic #_rate
		comm_cost=self.module.modules_list[m].comm_cost_per*self.host_traffic_demand_dict[h]
		link_cost=comm_cost/Switch.no_level_2_switches
		return comm_cost,link_cost

	def get_flow_size_for_host_route(self,host):
		#return flow-BW for each core
		if self.flow_distribuation==EQUAl_FLOW_DISTRIBUTION:
			flowsize=self.host_traffic_demand_dict[host]/Switch.no_level_2_switches
		else:
			print ("Error flow_distribuation is not equal")
			exit()
		return flowsize
	
	def get_statless_vs_stateful_per(self,module_list):
		stateless=0
		stateful=0
		for module in module_list:
			if(self.module.modules_list[module].type==STATELESS):
				stateless+=self.module.modules_list[module].size
			elif(self.module.modules_list[module].type==STATEFUL):
				stateful+=self.module.modules_list[module].size
		total=stateless+stateful
		return stateless/total,stateful/total
				
			
	def build_requests(self):
		#this function purpose to build to data structure 
		#self.requests_dict
		#requests_h_m_dict_dict
		########the following dict of dict of request objects
		requests_h_m_dict_dict={}
		for host_index in range(Host.no_of_hosts):
			requests_h_m_dict_dict[host_index]={}
			######Chains goes here
			while(1):
				modules_list=get_sample([x for x in range(Module.number_of_modules)],self.host_modules_request_rate)
				if(Module.stateless_modules_per!=0.5 or self.host_modules_request_rate<=3):
					break
				(stateless_per,stateful_per)=self.get_statless_vs_stateful_per(modules_list)
				if((stateless_per>stateful_per+0.2)or(stateless_per<stateful_per-0.2)):
						continue
				break

			###################Create requests
			for module in modules_list:
				(basline_cost,traffic_cost,switches_cost_list)=self.get_computing_cost(host_index,module)
				(comm_cost,link_cost)=self.get_communication_and_link_cost(host_index,module)
				Req=Request(host_index,module,basline_cost,traffic_cost,comm_cost,switches_cost_list,link_cost)
				requests_h_m_dict_dict[host_index][module]=Req
				self.requests_dict[(host_index,module)]=Req
				self.requested_R+=Req.switches_cost_list[MAIN_INSTANCE_LEVEL0]
				if(self.module.modules_list[module].type==STATELESS):
					self.requested_R_stateless+=Req.switches_cost_list[MAIN_INSTANCE_LEVEL0]
				elif(self.module.modules_list[module].type==STATEFUL):
					self.requested_R_stateful+=Req.switches_cost_list[MAIN_INSTANCE_LEVEL0]
		return  requests_h_m_dict_dict

	def build_requests_for_single_clss_type(self,scenario_object,class_type):
		#this function purpose to build to data structure 
		#self.requests_dict
		#requests_h_m_dict_dict
		requests_h_m_dict_dict={}
		
		for host_index in range(Host.no_of_hosts):
			requests_h_m_dict_dict[host_index]={}
			for module in scenario_object.requests_h_m_dict_dict[host_index]:
				if(self.module.modules_list[module].type==class_type):
					requests_h_m_dict_dict[host_index][module]=scenario_object.requests_h_m_dict_dict[host_index][module]
					self.requests_dict[(host_index,module)]=scenario_object.requests_dict[(host_index,module)]
		return  requests_h_m_dict_dict

	def build_hosts_flow_demand(self):
		###make sure it is postive
		##### this valuesare real not percentage Host.traffic_rate_mean,Host.traffic_rate_stdev
		h_traffic_demand_dict={}
		for host in range(Host.no_of_hosts):
			h_traffic_demand_dict[host]=draw_number_from_normal_distribuation_in_limits(Host.traffic_rate_mean,Host.traffic_rate_stdev)

		return h_traffic_demand_dict

	def sort_requests_by_order(self,order,requests_dict):
	
		#order is (DEC_computing,ASC_computing, DEC_communication ,DEC_comp+comm, DEC_stateless_computing, DEC_stateful_computing, RAN)
		#if request_dict are empty return empty
		request_tuple_list=[]
		if(not requests_dict):
			return request_tuple_list
		for (h,m) in requests_dict:
			computing_cost=self.requests_h_m_dict_dict[h][m].baseline_cost+self.requests_h_m_dict_dict[h][m].traffic_cost
			##### Order tuple(type,comp cost,comm cost,comp+comm cost,host,module )
			request_tuple=(self.module.modules_list[m].type,computing_cost,self.requests_h_m_dict_dict[h][m].comm_cost,computing_cost+self.requests_h_m_dict_dict[h][m].comm_cost,h,m)
			request_tuple_list.append(request_tuple)
					
		shuffle(request_tuple_list)
		if order==ORDERED_BY_RANDOM:
			pass
		#ORDERED_BY_COMP_DEC ==> requests in DEC order by computing resourecs	
		elif order==ORDERED_BY_COMP_DEC:
			#request_tuple_list.sort(key = lambda x: (x[1],x[2]),reverse=True)
			request_tuple_list.sort(key = lambda x: (x[1]),reverse=True)
		#ORDERED_BY_COMM_DEC ==> requests in DEC order by communication resourecs
		elif order==ORDERED_BY_COMM_DEC:
			request_tuple_list.sort(key = lambda x: (x[2]),reverse=True)
		#ORDERED_BY_COMP_PLUS_COMM ==> requests in DEC order by computing + communication resourecs
		elif order==ORDERED_BY_COMP_PLUS_COMM:
			request_tuple_list.sort(key = lambda x: (x[3]),reverse=True)
		#ORDERED_BY_COMP_DEC_STATELESS_FIRST ==> requests in DEC order by type(statless then stateful) then computing resourecs
		elif order==ORDERED_BY_COMP_DEC_STATELESS_FIRST:
			request_tuple_list.sort(key = lambda x: (x[1]),reverse=True)
			request_tuple_list.sort(key = lambda x: (x[0]))
		#ORDERED_BY_COMP_DEC_STATEFUL_FIRST ==> requests in DEC order by type(statleful then stateless) then computing resourecs
		elif order==ORDERED_BY_COMP_DEC_STATEFUL_FIRST:
			request_tuple_list.sort(key = lambda x: (x[0],x[1]),reverse=True)
		#ORDERED_BY_COMP_ASC==> requests in ASC order by computing resourecs	
		elif order==ORDERED_BY_COMP_ASC:
			request_tuple_list.sort(key = lambda x: (x[1]))
		elif order==ORDERED_BY_RANDOM_STATEFUL_FIRST:
			request_tuple_list.sort(key = lambda x: (x[0]),reverse=True)
		else:
			print("ERRRRRRoR in sorting")
			exit()
		#print (request_tuple_list)	
		return request_tuple_list
	
	
	

if __name__ == '__main__':
	
	files={"path":"Result/"}
	Fat_tree={"k":4}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	modules={"max_size_of_module":switches["rack_capacity"]/1,"stateless_modules_per":0.5,
	"number_of_modules":20,"modules_size_mean_per":0.1,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.2,"comm_cost_stdev_per":0.1}
	
	scenario={"host_modules_request_rate":1,"modules_baseline_per":0.5,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}

	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	#S.sort_requests_by_order(self,order):
	print (S.requested_R_stateless/S.requested_R)
	print (S.requested_R_stateful/S.requested_R)

	print (S.sort_requests_by_order(ORDERED_BY_RANDOM_STATEFUL_FIRST,S.requests_dict))
	#print vars(T)
	print ("ok")
