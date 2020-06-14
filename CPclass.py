from CPMainclass import *
from docplex.cp.model import CpoModel

class CP_Allocation(CP_Main_Allocation):
	
	def __init__(self,scenario,algorithm,cp_parameters,scenario_parameters,switches_online_capacity,links_online_capacity):
		
		super(CP_Allocation, self).__init__(scenario,algorithm,cp_parameters,switches_online_capacity,links_online_capacity)
		####################################################requestes scenario Data structure(modules)
		self.timeout=cp_parameters["timeout"]
		self.trace_log=cp_parameters["trace_log"]
		self.workers=cp_parameters["workers"]
		self.msol={}
		
		add_to_file(self,'a',"\nStart allocation process for "+str(ALGORITHMS_NAMES[self.algorithm]),self.tree.trace,False)

		#algorithm=ALGORITHM_CP_COMP
		# ALGORITHM_CP_COMM , ALGORITHM_CP_COMP_PLUS_COMM , ALGORITHM_CP_STATEFUL_PERC
		if self.algorithm in [ALGORITHM_CP_STATEFUL_PERC,ALGORITHM_CP_STATELESS_PERC] :
			if self.algorithm ==ALGORITHM_CP_STATELESS_PERC:
				phase_1_class=STATELESS
				phase_2_class=STATEFUL
				phase_1_algorithm=ALGORITHM_CP_COMP
				phase_2_algorithm=ALGORITHM_CP_COMM
			else:

				phase_1_class=STATEFUL
				phase_2_class=STATELESS
				phase_1_algorithm=ALGORITHM_CP_COMM
				phase_2_algorithm=ALGORITHM_CP_COMP
			
			phase_1_scenario=Scenario(module=self.module,scenario_parameters=scenario_parameters,scenario_object=scenario,class_type=phase_1_class)
			if(phase_1_scenario.requests_dict):
				#######create CP_allocation with out initial online capacity
				phase_1_allocation=CP_Allocation(scenario=phase_1_scenario,algorithm=phase_1_algorithm,cp_parameters=cp_parameters,scenario_parameters=scenario_parameters,
				switches_online_capacity={},links_online_capacity={})
				self.update_allocation_after_solving_cp(phase_1_allocation.X,phase_1_allocation.msol,phase_1_allocation.cp_locations)
				#	A=[]
				#	R=[]
				phase_2_scenario=Scenario(module=self.module,scenario_parameters=scenario_parameters,scenario_object=scenario,class_type=phase_2_class)
				if(phase_2_scenario.requests_dict):
					phase_2_allocation=CP_Allocation(scenario=phase_2_scenario,algorithm=phase_2_algorithm,cp_parameters=cp_parameters,scenario_parameters=scenario_parameters,
					switches_online_capacity=phase_1_allocation.switches_online_capacity,links_online_capacity=phase_1_allocation.links_online_capacity)
					self.update_allocation_after_solving_cp(phase_2_allocation.X,phase_2_allocation.msol,phase_2_allocation.cp_locations)
				else:
					print ("error in CP no requests 1")
					exit()
				phase_1_scenario=[]
				phase_1_allocation=[]
				phase_2_scenario=[]
				phase_2_allocation=[]
				
			else:
				print ("error in CP no requests 2")
				exit()
				self.cpmodel.minimize(self.S_Obj)
				self.msol = self.cpmodel.solve(TimeLimit=self.timeout,trace_log=self.trace_log,Workers=self.workers,FailureDirectedSearchEmphasis=1)
				print (self.msol.get_objective_values())
				print (self.msol.is_solution_optimal())
				self.update_allocation_after_solving_cp(self.X,self.msol,self.cp_locations)
				#phase_2_allocation=CP_Allocation(scenario=phase_1_scenario,algorithm=ALGORITHM_CP_COMM,allocation_file_parameters=Allocation_files,cp_parameters=cp,
		else:
			if self.algorithm==ALGORITHM_CP_COMP:
				self.cpmodel.minimize(self.S_Obj)
				self.msol = self.cpmodel.solve(TimeLimit=self.timeout,trace_log=self.trace_log,Workers=self.workers,FailureDirectedSearchEmphasis=1)#Restart SearchType="MultiPoint")#
				#FailureDirectedSearchEmphasis=1
			elif self.algorithm==ALGORITHM_CP_COMM:
				self.cpmodel.minimize(self.L_Obj )
				self.msol = self.cpmodel.solve(TimeLimit=self.timeout,trace_log=self.trace_log,Workers=self.workers,FailureDirectedSearchEmphasis=1)
			elif self.algorithm==ALGORITHM_CP_COMP_PLUS_COMM:
				self.cpmodel.minimize(self.S_Obj+self.L_Obj)
				#self.msol = self.cpmodel.solve(TimeLimit=self.timeout,trace_log=self.trace_log,Workers=self.workers,FailureDirectedSearchEmphasis=1)
				self.msol = self.cpmodel.solve(trace_log=self.trace_log,Workers=2)
			self.update_allocation_after_solving_cp(self.X,self.msol,self.cp_locations)
		if(self.msol):
			print (self.msol.get_objective_values())
			print (self.msol.is_solution_optimal())
		add_to_file(self,'a',"\nAllocation for "+str(ALGORITHMS_NAMES[self.algorithm])+" Completed",self.tree.trace,False)



if __name__ == '__main__':
	
	Fat_tree={"k":4}
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
	
	
	cp={"timeout":30,"trace_log":True,"workers":4}

	parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	"Requested_R_per"]
	
	
	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	#algorithm=ALGORITHM_CP_COMP
	algorithm=ALGORITHM_CP_STATEFUL_PERC
	# ALGORITHM_CP_COMM , ALGORITHM_CP_COMP_PLUS_COMM , ALGORITHM_CP_STATEFUL_PERC
	A=CP_Allocation(scenario=S,algorithm=algorithm,cp_parameters=cp,scenario_parameters=scenario,switches_online_capacity={},links_online_capacity={})
	
	print ("OK")
	#print vars(A)
						
