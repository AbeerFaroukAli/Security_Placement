from Greedyclass import *

class TABU_Allocation(Greedy_Allocation):
	
	def __init__(self,scenario,algorithm,tabu_parameters):
		
		self.iteration=tabu_parameters["iterations"]
		self.tabu_list_len=tabu_parameters["tabu_list_len"]
		self.diff=2
		if(algorithm in TABU_BFD_ALGORITHMS_LIST ):
			initial_solution_algorithm=ALGORITHM_BFD
			super(TABU_Allocation, self).__init__(scenario,initial_solution_algorithm)
		elif(algorithm in TABU_RANDOM_ALGORITHMS_LIST):
			initial_solution_algorithm=ALGORITHM_RANDOM
			super(TABU_Allocation, self).__init__(scenario,initial_solution_algorithm)
		else:
			print ("error in Tabu algorithms")
			exit()
		sum0=sum(self.switches_online_capacity.values())	
		if algorithm in TABU_BFD_ALGORITHMS_LIST:
			req=self.get_all_unallocated_requests()
			L1=len(req)
		
		self.algorithm=algorithm
		self.get_tabu_allocation()
		
		if algorithm in TABU_BFD_ALGORITHMS_LIST:
			req=self.get_all_unallocated_requests()
			L2=len(req)
			if(L2>L1):
				print ("Error in unalloctaed in tabu")
				exit()
			
		
	def get_tabu_allocation(self):
		
		add_to_file(self,'a',"\nStart allocation process for "+str(ALGORITHMS_NAMES[self.algorithm]),self.tree.trace,False)
		request_list=self.sort_requests()
		no_of_reqs=len(request_list)
		max_iterations=self.iteration
		tabu_list=[]
		i=0
		tabu_list_len=no_of_reqs
		#self.tabu_list_len
		
		while(1):
			next_move_found=False
			#####################iteration
			#########sort requests decending
			sum1=sum(self.switches_online_capacity.values())
			for mtype,comp_cost,comm_cost,total_cost,h,m in request_list:
				move_found=False
				if(self.h_m_allocation_dict_dict[h][m]==UN_ALLOCATED):
					self.tabu_allocate_req(h,m) 
					continue
				if((h,m) in tabu_list):
					continue
				move_found,move_type,move_tuple,s_gain,l_gain=self.get_next_move(h,m)
				if(move_found):
					#print ("new move found")
					next_move_found=True
					#print (h,m,move_type,s_gain,l_gain)
					self.update_next_move(h,m,move_type,move_tuple)
					tabu_list.append((h,m))
					break
			sum2=sum(self.switches_online_capacity.values())
			
			####Aspiration rule
			if not next_move_found:
				best_s_gain=0
				best_l_gain=0
				for h,m in tabu_list:
					move_found=False
					move_found,move_type,move_tuple,s_gain,l_gain=self.get_next_move(h,m)
					if(move_found):
						if(best_s_gain+self.diff<s_gain and best_l_gain<=l_gain) or (best_s_gain<=s_gain and best_l_gain+self.diff<l_gain) :
							next_move_found=True
							best_h=h
							best_m=m
							best_move_type=move_type
							best_move_tuple=move_tuple
							best_s_gain=s_gain
							best_l_gain=l_gain		
				if(next_move_found):
					self.update_next_move(best_h,best_m,best_move_type,best_move_tuple)
					#print ("new move found in tabu")
			sum3=sum(self.switches_online_capacity.values())
			########check if no more moves terminate
			if(next_move_found==False):
				#print ("ended by no more moves found")
				break
			#####################Memory structure
			if(i>tabu_list_len):
				tabu_list=tabu_list[1:]
			#######################terminate on reaching iteration limit
			i+=1
			if(i>max_iterations):
				print ("ended by max iteration")
				break
		add_to_file(self,'a',"\nAllocation for "+str(ALGORITHMS_NAMES[self.algorithm])+" Completed",self.tree.trace,False)
		
		
	def update_next_move(self,h1,m1,move_type,move_tuple):
		
		sum1=sum(self.switches_online_capacity.values())
		self.unallocate_req(h1,m1)
		if(move_type==TABU_MOVE):
			req_allocation_1=move_tuple
			self.update_allocation(h1,m1,req_allocation_1)
			sum3=sum(self.switches_online_capacity.values())
			if(sum1>=sum3):
				print ("error in update next move",sum1,sum3,h,m)
				exit()
			
			
			#print ("move update")
		elif(move_type==TABU_SINGLE_SWAP):
			h2,m2,req_allocation_1,req_allocation_2=move_tuple
			self.unallocate_req(h2,m2)
			self.update_allocation(h1,m1,req_allocation_1)
			self.update_allocation(h2,m2,req_allocation_2)
			#print ("single swap update")
		else:
			print ("Error in update_next_move in TABU unvalid move")
		
	def tabu_allocate_req(self,h,m):
		
		###this function for unallocated requests
		next_move_found=False
		next_move_found,req_allocation=self.find_valid_allocation(h,m,LEVEL0)
		if(not next_move_found):
			next_move_found,req_allocation=self.find_valid_allocation(h,m,LEVEL1)
			if(not next_move_found):
				next_move_found,req_allocation=self.find_valid_allocation(h,m,LEVEL2)
				
		if(next_move_found):
			#print ("unallocated updateted in next move")
			self.update_allocation(h,m,req_allocation)
		return next_move_found
	
	def get_next_move(self,h,m):
		
		move_type=-1
		move_tuple=-1
		s_gain=0
		l_gain=0
		
		next_move_found=False
		if (self.h_m_allocation_dict_dict[h][m] in [UN_ALLOCATED_YET,UN_ALLOCATED]):
			print ("error in tabu get_better_tabu_move - unallocated_yet or unallocated")
			exit()
		if(self.algorithm in [ALGORITHM_TABU_BFD_MOVE,ALGORITHM_TABU_RANDOM_MOVE]):
			move_type=TABU_MOVE
			next_move_found,req_allocation,s_gain,l_gain=self.get_better_TABU_LOWER(h,m)
			if(next_move_found):
				move_tuple=req_allocation
		elif(self.algorithm in [ALGORITHM_TABU_BFD_SINGLE_SWAP,ALGORITHM_TABU_RANDOM_SINGLE_SWAP]):
			move_type=TABU_SINGLE_SWAP
			next_move_found,h2,m2,req_all_1,req_all_2,s_gain,l_gain=self.get_better_TABU_SINGLE_SWAP(h,m)
			if(next_move_found):
				move_tuple=(h2,m2,req_all_1,req_all_2)
		elif(self.algorithm in [ALGORITHM_TABU_BFD_ALL_MOVES,ALGORITHM_TABU_RANDOM_ALL_MOVES]):
			next_move_found,move_type,move_tuple,s_gain,l_gain=self.get_better_all_moves(h,m)
		else:
			print ("Error in get next move in Tabu not valid algorithms")
			exit()
		
		return next_move_found,move_type,move_tuple,s_gain,l_gain
	
	def get_better_TABU_LOWER(self,h,m):
		
		sum1=sum(self.switches_online_capacity.values())
		
		if (self.h_m_allocation_dict_dict[h][m] in [UN_ALLOCATED_YET,UN_ALLOCATED]):
			print ("error in tabu get_better_move - unallocated_yet or unallocated")
			exit()
			
		next_move_found=False
		new_req_allocation=0
		
		old_level=self.h_m_allocation_dict_dict[h][m].level
		#########no better move
		if(old_level==LEVEL0):
			return False,0,0,0
		old_req_allocation=self.h_m_allocation_dict_dict[h][m]
		old_s_cost=self.h_m_allocation_dict_dict[h][m].total_comp_cost
		old_l_cost=self.h_m_allocation_dict_dict[h][m].total_comm_cost
		temp=deepcopy(self)
		temp.unallocate_req(h,m)
		
		
		if(old_level==LEVEL1):	
			next_move_found,new_req_allocation=temp.find_valid_allocation(h,m,LEVEL0)
		elif(old_level==LEVEL2):
			next_move_found,new_req_allocation=temp.find_valid_allocation(h,m,LEVEL0)
			if(next_move_found==False):
				next_move_found,new_req_allocation=temp.find_valid_allocation(h,m,LEVEL1)

		if(next_move_found):
			new_s_cost=new_req_allocation.total_comp_cost
			new_l_cost=new_req_allocation.total_comm_cost
			s_gain=old_s_cost-new_s_cost
			l_gain=old_l_cost-new_l_cost
		else:
			s_gain=0
			l_gain=0
		sum2=sum(self.switches_online_capacity.values())
		if(sum1!=sum2):
			print ("error in get better tabu move")
			exit()
		
		return next_move_found,new_req_allocation,s_gain,l_gain
	
	def get_better_TABU_SINGLE_SWAP(self,h1,m1):
		
		if(self.h_m_allocation_dict_dict[h1][m1] in [UN_ALLOCATED_YET,UN_ALLOCATED]):
			print ("error in tabu get_better_single_swap unallocated_yet or unallocated")
			exit()

		original_level=self.h_m_allocation_dict_dict[h1][m1].level
		
		swap_requests=self.get_requests_valid_for_swap(h1,m1)
		best_swap_found=False
		best_swap_tuple=(False,0,0,0,0)
		best_s_gain=0
		best_l_gain=0

		
		for (h2,m2) in swap_requests:
			old_req_allocation1=self.h_m_allocation_dict_dict[h1][m1]
			old_req_allocation2=self.h_m_allocation_dict_dict[h2][m2]
			if(old_req_allocation2==UN_ALLOCATED):
				continue
			if(old_req_allocation1.level==old_req_allocation2.level):
				continue
			temp_allocation=deepcopy(self)
			temp_allocation.unallocate_req(h1,m1)
			temp_allocation.unallocate_req(h2,m2)
			
			valid1,req_allocation1=temp_allocation.find_valid_allocation(h1,m1,old_req_allocation2.level)
			if(valid1):
				temp_allocation.update_allocation(h1,m1,req_allocation1)
				valid2,req_allocation2=temp_allocation.find_valid_allocation(h2,m2,old_req_allocation1.level)
				if(valid2):
					temp_allocation.update_allocation(h2,m2,req_allocation2)

			if( (not valid1) or (not valid2)):
				continue
			old_req_allocation1_s_cost=old_req_allocation1.total_comp_cost
			old_req_allocation1_l_cost=old_req_allocation1.total_comm_cost
			
			old_req_allocation2_s_cost=old_req_allocation2.total_comp_cost
			old_req_allocation2_l_cost=old_req_allocation2.total_comm_cost
					
			old_s_cost=old_req_allocation1_s_cost+old_req_allocation2_s_cost
			old_l_cost=old_req_allocation1_l_cost+old_req_allocation2_l_cost
					
			new_s_cost=req_allocation1.total_comp_cost+req_allocation2.total_comp_cost
			new_l_cost=req_allocation1.total_comm_cost+req_allocation2.total_comm_cost
			cost_s_gain=old_s_cost-new_s_cost
			cost_l_gain=old_l_cost-new_l_cost
			if(best_s_gain+self.diff<cost_s_gain and best_l_gain<=cost_l_gain) or (best_s_gain<=cost_s_gain and best_l_gain+self.diff<cost_l_gain) :
				best_swap_tuple=(True,h2,m2,req_allocation1,req_allocation2)
				best_s_gain=cost_s_gain
				best_l_gain=cost_l_gain

		best_swap_found,h2,m2,new_req_allocation1,new_req_allocation2=best_swap_tuple
		if( not best_swap_found):
			#print ("swap not found")
			return False,0,0,0,0,0,0
		return best_swap_found,h2,m2,new_req_allocation1,new_req_allocation2,best_s_gain,best_l_gain
	
	def get_better_all_moves(self,h,m):
		
		next_move_found=False
		move_found,move_req_all,move_s_gain,move_l_gain=self.get_better_TABU_LOWER(h,m)
		single_swap_found,single_swap_h2,single_swap_m2,single_swap_req_all_1,single_swap_req_all_2,single_swap_s_gain,single_swap_l_gain=self.get_better_TABU_SINGLE_SWAP(h,m)
		winner=-1
		if(move_found or single_swap_found):
			next_move_found=True
		if(move_found and single_swap_found):
			if(move_s_gain>=single_swap_s_gain and move_l_gain>single_swap_l_gain) or (move_s_gain>single_swap_s_gain and move_l_gain>=single_swap_l_gain):
				winner=TABU_MOVE
			else:
				winner=TABU_SINGLE_SWAP
		elif(move_found and (not single_swap_found)):
			winner=TABU_MOVE
		elif((not move_found) and single_swap_found):
			winner=TABU_SINGLE_SWAP
		
		else:
			return False,-1,-1,-1,-1
		
		if(winner==TABU_MOVE):
			move_type=TABU_MOVE
			s_gain=move_s_gain
			l_gain=move_l_gain
			move_tuple=move_req_all
		elif(winner==TABU_SINGLE_SWAP):
			move_type=TABU_SINGLE_SWAP
			s_gain=single_swap_s_gain
			l_gain=single_swap_l_gain
			move_tuple=single_swap_h2,single_swap_m2,single_swap_req_all_1,single_swap_req_all_2
		else:
			print ("error in move all")
			exit()			
	
		return  next_move_found,move_type,move_tuple,s_gain,l_gain
	
	def get_requests_valid_for_swap(self,h,m):
		
		if(self.h_m_allocation_dict_dict[h][m] in [UN_ALLOCATED_YET,UN_ALLOCATED]):
			print ("error in tabu get_requests_valid_for_swap- unallocated_yet or unallocated")
			exit()
			
		requests_list=[]
		old_req_allocation=self.h_m_allocation_dict_dict[h][m]
		
		if(old_req_allocation.level==LEVEL0 ):
			for (h1,m1) in self.scenario.requests_dict:
				if(self.tree.hosts_list[h].parent_switches[LEVEL0]==self.tree.hosts_list[h1].parent_switches[LEVEL0]):
					if(self.h_m_allocation_dict_dict[h1][m1]==UN_ALLOCATED):
						requests_list.append((h1,m1))
					elif(self.h_m_allocation_dict_dict[h1][m1].level in [LEVEL1,LEVEL2]):
						requests_list.append((h1,m1))
					
		if(old_req_allocation.level==LEVEL1):
			for (h1,m1) in self.scenario.requests_dict:
				if(self.tree.hosts_list[h].pod_index==self.tree.hosts_list[h1].pod_index):
					if(self.h_m_allocation_dict_dict[h1][m1]==UN_ALLOCATED):
						requests_list.append((h1,m1))
					elif(self.h_m_allocation_dict_dict[h1][m1].level in [LEVEL2,LEVEL0]):
						requests_list.append((h1,m1))
						
		if(old_req_allocation.level==LEVEL2):
			for (h1,m1) in self.scenario.requests_dict:
				if(self.h_m_allocation_dict_dict[h1][m1]==UN_ALLOCATED):
						requests_list.append((h1,m1))
				elif(self.h_m_allocation_dict_dict[h1][m1].level in [LEVEL0,LEVEL1]):
						requests_list.append((h1,m1))
	
		return requests_list
		
	def find_best_allocation_not_in_level(self,h,m,level):

		level_list=[LEVEL0,LEVEL1,LEVEL2]
		level_list.remove(level)
	
		valid1,req_allocation1=self.find_valid_allocation(h,m,level_list[0])
		if(valid1):
			return valid1,req_allocation1
		
		else:
			valid2,req_allocation2=self.find_valid_allocation(h,m,level_list[1])
			return valid2,req_allocation2


if __name__ == '__main__':
	
	Fat_tree={"k":6}
	files={"path":"Result/"}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.8,"host_flow_rate_stdev_per":0.1}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	
	scenario={"host_modules_request_rate":4,"modules_baseline_per":0.9,"flow_distribuation":EQUAl_FLOW_DISTRIBUTION}

	modules={"max_size_of_module":switches["rack_capacity"]/scenario["host_modules_request_rate"],"stateless_modules_per":0.5,
	"number_of_modules":20,"modules_size_mean_per":0.8,"modules_size_stdev_per":0.1,
	"comm_cost_mean_per":0.2,"comm_cost_stdev_per":0.1}
	
	cp={"timeout":400,"trace_log":False,"workers":2}
	tabu={"iterations":200,"tabu_list_len":50}
	near_optimal={"timeout":150,"trace_log":False}
	
	parameter_list=["Total_m","Allocated_m","Un_allocated_m_per","allocated_m_Level_1_per","allocated_m_Level_2_per","allocated_m_Level_0_per","Overhead_consumed_L_R_weighted_per over consumed",
	"over_ratio_weighted_only_over_links","over_ratio_weighted_All_links","over_ratio_only_over_links","over_ratio_All_links","Requested_R_per"]

	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=False)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	S=Scenario(module=M,scenario_parameters=scenario,scenario_object={},class_type={})
	
	#S.requests.request

	algorithm=ALGORITHM_TABU_RANDOM_ALL_MOVES
	tabu={"iterations":200,"tabu_list_len":len(S.requests_dict)}
	
	A=TABU_Allocation(scenario=S,algorithm=algorithm,tabu_parameters=tabu)

	
	print ("OK")
	#print vars(A)
						
