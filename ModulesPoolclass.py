#from docplex.cp.model import CpoModel

from Fattreeclass import *
#import itertools
###########Architecture +modules+flow+requests+

class Modules_Pool(object):

	def get_module_type(self):
		number=random()
		if(number>=Module.stateless_modules_per):
			return STATEFUL
		else:
			return STATELESS

	def get_type_list(self):
		
		#print(math.ceil(4.2))
		no_of_statless=ceil(Module.number_of_modules*Module.stateless_modules_per)
		stateless_list=get_sample([i for i in range(Module.number_of_modules)],no_of_statless)

		type_list=[]
		for index in range(Module.number_of_modules):
			if index in stateless_list:
				type_list.append(STATELESS)
			else:
				type_list.append(STATEFUL)
		
		#######chech and print numbers
		type1=0
		type2=0
		for index in range(Module.number_of_modules):
			if type_list[index] ==STATELESS:
				type1+=1
			if type_list[index] ==STATEFUL:
				type2+=1
		return type_list

	def build_modules(self,modules_parameters):
		
		Module.max_size_of_module=modules_parameters["max_size_of_module"]
		Module.number_of_modules=modules_parameters["number_of_modules"]
		Module.size_mean=modules_parameters["modules_size_mean_per"] * Module.max_size_of_module   	
		Module.size_stdev=modules_parameters["modules_size_stdev_per"] * Module.max_size_of_module
		Module.communication_mean=modules_parameters["comm_cost_mean_per"]
		Module.communication_stdev=modules_parameters["comm_cost_stdev_per"]
		Module.stateless_modules_per=modules_parameters["stateless_modules_per"]
		Module.module_parameters=modules_parameters
		type_list=self.get_type_list()
		modules_list=[]
		

		for index in range(Module.number_of_modules):			
			name='m'+str(index)
			module_type=type_list[index]
			size=draw_number_from_normal_distribuation_in_limits(Module.size_mean,Module.size_stdev)
			if(size==0):
				print ("error in modules module size=0")
				exit()
			if(module_type==STATELESS):
				comm_cost_per=0
			else:
				comm_cost_per=draw_number_from_normal_distribuation_in_limits(Module.communication_mean,Module.communication_stdev)

			module=Module(index,name,module_type,size,comm_cost_per)
			modules_list.append(module)

		return modules_list
			
	def __init__(self,tree,modules_parameters):
		
		self.tree=tree
		self.file=self.tree.files_path+"Module.txt"
		####Build modules
		self.modules_list=self.build_modules(modules_parameters)
		#######################################################
		add_to_file(self,'w',
			"k="+str(tree.k)
			+str("\nModules parameters")+str(Module.module_parameters)
			+str("\n #M="+str([m.__dict__ for m in self.modules_list])),self.tree.trace,False)			
		#print ("==========>Scenario Module Created")
	

if __name__ == '__main__':
	
	########### Fat tree Architecture
	Fat_tree={"k":8}
	#####writing_mode='w' or 'a'====> w mean erase old files while 'a' mean extend  already exist files
	files={"path":"Result/"}
	#module_files={"files_path":"Result/","file_name":"Module.txt"}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	### Hint max_size_of_module=switches=["capacity_of_switch_in_level_0"]
	request_rate=5
	modules={"max_size_of_module":switches["rack_capacity"]/request_rate,"stateless_modules_per":0.5,
	"number_of_modules":3,"modules_size_mean_per":0.5,"modules_size_stdev_per":0.1,
	"baseline_per":0.5,"comm_cost_mean_per":0.5,"comm_cost_stdev_per":0.1}
	#Hint max traffic rate of host=links["BW_Links_in_Level_list"][LEVEL1]
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	M=Modules_Pool(tree=T,modules_parameters=modules)
	#print S.sort_by_request('DEC_type1_total',Error_file="Result/Error_file.txt")
	#print vars(T)
	print ("ok")

#   print [T.x for x in dir(T)]
