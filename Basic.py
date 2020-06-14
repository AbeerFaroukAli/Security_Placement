from constant import*
import networkx as nx
import numpy as np
from random import sample
from math import ceil

########### Fat tree Architecture

class Switch(object):

    ## list of switches names in order of general index
    capacity_of_switches_in_level_0_new=0
    capacity_mode=0 #or VARIABLE
    switch_parameters={}

    #### exampe [0]=[s1,s2,...] , [1]=[s8,s9...]
   
    def __init__(self,k,name,level,index,index_in_level,pod_index):

        self.name=name
        self.level=level
        self.index=index
        self.index_in_level=index_in_level
        self.pod_index=pod_index
        if(Switch.capacity_mode=="FIXED"):
            self.capacity=Switch.capacity_of_switches_in_level_0_new
        elif(Switch.capacity_mode=="VARIABLE"):
            if(self.level==LEVEL0):
                self.capacity=Switch.capacity_of_switches_in_level_0_new
            elif(self.level==LEVEL1):
                self.capacity=(((k/2)+1)/4+(3/4))*Switch.capacity_of_switches_in_level_0_new
               # self.capacity=(((k/2)+1)/4+((1+((k/2-1)/(k/2))))/4)*Switch.capacity_of_switches_in_level_0_new
            elif(self.level==LEVEL2):
               self.capacity=(((k/2)**2+1)/2+(3/2))*Switch.capacity_of_switches_in_level_0_new
              # self.capacity=(((k/2)**2+1)/2+((1+((k/2-1)/(k/2))))/2)*Switch.capacity_of_switches_in_level_0_new
            else:
                print("Error Unknown Level in Switches Capacity")
                exit()
        else:

            print("Error Unknown capacity mode in Switches Capacity")
            exit()
    
class Host(object):

    no_of_hosts_per_switch=0
    no_of_hosts=0
    max_traffic_rate=0
    traffic_rate_mean=0
    traffic_rate_stdev=0
    host_parameters={}

    def __init__(self,name,index,pod,TOR_switch,agg_switches,parent_switches,ECMP_traffic_routes):

        self.name=name
        self.index=index
        self.pod_index=pod
        self.TOR_switch_index=TOR_switch
        self.agg_switches=agg_switches
        # this variable indicate the switches that predecessor a ceratin host
        #### example [0]=[s1,s2,...] , [1]=[s8,s9...] [2]=[s]
        self.parent_switches=parent_switches
        self.ECMP_traffic_routes=ECMP_traffic_routes

class Link(object):

    number_of_links=0
    oversubscription_ratio=0
    
	############all links are down direction
    def __init__(self,name,level,start_switch_index,end_switch_index,weight,bandwidth):
        #name is an ordered pair of switches ('s1','s2')
        self.name=name
        self.level=level
        self.start_switch=start_switch_index
        self.end_switch=end_switch_index
        self.weight=weight
        self.bandwidth=bandwidth
        self.bandwidth_with_ovs=bandwidth*Link.oversubscription_ratio

class Module(object):
    
    max_size_of_module=0
    number_of_modules=0
    size_mean=0
    size_stdev=0
    communication_mean=0
    communication_stdev=0
    stateless_modules_per=0
    module_parameters={}
    
    def __init__(self,index,name,module_type,size,communication_cost_per):
        
        self.index=index
        self.name=name
        self.type=module_type
        self.size=size
        #########communciation cost is a percenatge of traffic rate
        self.comm_cost_per=communication_cost_per
		
class Request(object):

    modules_request_rate=0
    def __init__(self,h,m,baseline_cost,traffic_cost,comm_cost,switches_cost_list,link_cost):

        self.name_tuple=(h,m)
        self.host=h
        self.module=m
        self.baseline_cost=baseline_cost
        self.traffic_cost=traffic_cost 
        self.comm_cost=comm_cost     #for hole traffic
        self.switches_cost_list=switches_cost_list
        ############single link in level 2
        self.link_cost=link_cost
        self.total_switches_cost=[0,0,0,0]
        self.total_links_cost=[0,0,0]


class Request_Allocation(object):
    
    def __init__(self,level,switches_cost_dict,links_cost_list,flows_replacement={},parent_replacement={}):
		
		#########switches cost dict example  {s1:5,s2:8....}
        #########links_cost_list list of pair tuple example[([17, 12, 16], 4.75), ([19, 9, 0, 8, 16], 4.75)
        #########flows_replacement  #Flow_replacements_list_tuple [(oldpath,newpath,size)]
        #########parent_replacement_list_tuple #parent_replacement_list_tuple=[(1,s2),(2,s5),....]
        #self.index=index
        self.level=level
        self.switches_cost_dict=switches_cost_dict
        self.links_cost_list=links_cost_list
        self.flows_replacement=flows_replacement
        self.parent_replacement=parent_replacement
        self.total_comp_cost=sum(self.switches_cost_dict.values())
        self.total_comm_cost=0
        for route,cost in self.links_cost_list:
            no_of_links_in_route=len(route)-1
            self.total_comm_cost+=no_of_links_in_route*cost

class CP_Location(object):  ####this object is for CP only

	def __init__(self,index,level,switches,links,routes):
		
		self.index=index
		self.level=level
		############################switches= {s1:Mnitoring_level1}
		##########################to getcost =self.scenario.requests_dict[r].switches_cost_list[self.cp_locations[l].switches[s]]
		self.switches=switches
		###########################################################
		self.links=links       #################links={l1:number_of_links_in the allocation}
		########################
		self.routes=routes    ##################routes=[route1,route2,.....]
		
class LP_Location(object):  ####this object is for CP only

	def __init__(self,index,level,capacity,switches_dict):
		
		self.index=index
		self.level=level
		############################switches= {s1:Mnitoring_level1}
		##########################to getcost =self.scenario.requests_dict[r].switches_cost_list[self.cp_locations[l].switches[s]]
		self.capacity=capacity
		###########################################################
		self.switches_dict=switches_dict     #################links={l1:number_of_links_in the allocation}
		########################
        
def draw_number_from_normal_distribuation_in_limits(mean,stdev):
    number=np.random.normal(mean,stdev)
    ####################Make sure generated number is in limits
    while( (number>(mean+stdev)) or (number<(mean-stdev)) ):
        number=np.random.normal(mean,stdev)
    return number

def get_sample(List,number):
	
	new_list=sample(List,int(number))
	return new_list

def find_links_for_route(route):
		################## return links =list of tuples [(1,2),(3,5)]
		links=[]
		for j in range(len(route)-1):
			link=Link.mapping[(route[j],route[j+1])]
			links.append(link)
		return links

def find_switches_in_pod_in_level(pod_index,level):

    if(level in [LEVEL1,LEVEL0]):
        s_list=[s for s in Switch.switches_list_in_level[level][pod_index*Switch.no_of_switches_per_pod:(pod_index+1)*Switch.no_of_switches_per_pod]]
    else:
        print ("Error in pod switches")
        exit()
    return s_list

def add_to_file(class_object,writing_mode,string,traceflage,printflage):
    if(traceflage):
        OUT=open(class_object.file,writing_mode)
        OUT.write(string)
        OUT.close()
    if (printflage):
        print (string)

def add_to_output_file(filename,writing_mode,string,printflage):
	OUT=open(filename,writing_mode)
	OUT.write(string)
	OUT.close()
	if (printflage):
		print (string)

#def filter_networkx_graph_nodes(G,attribute,value):
#    return  [node for node,values in G.nodes.data(attribute) if values==value]
    
if __name__ == '__main__':
    Switch.capacity_mode="FIXED"
    s1=Switch(4,'s1',0,0,30,1)
    h1=Host('h1',0,1,[2],[[0],[1],[2]],2,[2,3])
    #name,startswitch,endswitch,weight,bandwidth,oversubscription_ratio):
    L1=Link('L1',1,1,2,1,1)
    print ("ok")
    #pid=os.getpid()
    #ps=psutil.Process(pid)
    #usage=ps.memory_info()
    #print (usage)
    draw_number_from_normal_distribuation_in_limits(1,1)
    #print (L1.__dict__ )
#   print [T.x for x in dir(T)]
    
