import json
from Basic import*
from random import random,shuffle,randint,normalvariate
from networkx.algorithms.shortest_paths.generic import shortest_path
#from networkx.algorithms.shortest_paths.generic import all_shortest_paths


class FatTree(object):

	def build_switches(self,switches_parameters):
		switches_list=[]
		#####Switches
		#switch static class variables
		Switch.capacity_of_switches_in_level_0_new=0.33*switches_parameters["rack_capacity"]*self.k/2
		Switch.capacity_mode=switches_parameters["capacity_mode"]
		Switch.switch_parameters=switches_parameters
		# Number of Edge (TOR) Switches=k^2/2
		Switch.no_level_0_switches=(self.k**2)//2
		#Number of Aggregation Switches=k^2/2
		Switch.no_level_1_switches=Switch.no_level_0_switches
		####Number of Core Switches=(k/2)^2
		Switch.no_level_2_switches=(self.k//2)**2
		#Number of Switches=5k^2/4
		Switch.no_of_switches=(5*(self.k**2))//4
		#Number of Switches/pod/layer=k/2
		Switch.no_of_switches_per_pod=self.k//2
		#Number of pods
		Switch.no_of_pods=self.k
		#############
		Switch.switches_list_in_level=[[],[],[]]
		

		###adding switches
		for switch_index in range(Switch.no_of_switches):
			name='s'+str(switch_index)
			level=0
			index_in_level=0
			if switch_index<Switch.no_level_0_switches:###Level 0 switches_list
				level=LEVEL0
				index_in_level=switch_index
				Switch.switches_list_in_level[level].append(switch_index)
			elif switch_index<Switch.no_level_1_switches+Switch.no_level_0_switches:
				level=LEVEL1
				index_in_level=switch_index%Switch.no_level_0_switches
				Switch.switches_list_in_level[level].append(switch_index)
			elif switch_index<Switch.no_level_2_switches+Switch.no_level_1_switches+Switch.no_level_0_switches:
				level=LEVEL2
				index_in_level=switch_index%Switch.no_level_1_switches
				Switch.switches_list_in_level[level].append(switch_index)
			else:
				print ("Error in Build switches")
				exit()
			pod_index=index_in_level//Switch.no_of_switches_per_pod
			
			switch=Switch(self.k,name,level,switch_index,index_in_level,pod_index)
			self.graph.add_node(switch.index,type=SWITCH_NODE,level=switch.level,name=switch.name,index_in_level=switch.index_in_level,capacity=switch.capacity)
			switches_list.append(switch)

		
		if ((len(switches_list)!=Switch.no_of_switches) or ((len(Switch.switches_list_in_level[LEVEL2])+len(Switch.switches_list_in_level[LEVEL1])+len(Switch.switches_list_in_level[LEVEL0]))!=Switch.no_of_switches)):
			print ("Error in number of switches")
			exit()

		return switches_list

	
	def build_links(self,links_parameters):

		#link
		links_dict={}
		##Number of links=k^3/2
		Link.number_of_links=(((self.k**3)//2)*2)/2
		Link.oversubscription_ratio=links_parameters["Oversubscription"]
		Link.parameters=links_parameters
		Link.mapping={}
		#links_node_pairs
		links_index=-1
		# TOR to Agg links
		level=LEVEL1
		for s_index in range(Switch.no_level_0_switches):
			start_index_of_pod=(s_index//Switch.no_of_switches_per_pod)*Switch.no_of_switches_per_pod
			for i in range(Switch.no_of_switches_per_pod):
				start_node=s_index
				end_node=Switch.no_level_0_switches+start_index_of_pod+i
				weight=links_parameters["Weight_Links_in_Level_list"][LEVEL1]
				BW=links_parameters["BW_Links_in_Level_list"][LEVEL1]
				#Down direction
				links_index+=1
				name='L'+str(links_index)
				link=Link(name,level,end_node,start_node,weight,BW)
				self.graph.add_edge(end_node,start_node,name=name,weight=weight,BW=BW,BW_with_sup=link.bandwidth_with_ovs)
				links_dict[(end_node,start_node)]=link
				Link.mapping[(start_node,end_node)]=(end_node,start_node)
				Link.mapping[(end_node,start_node)]=(end_node,start_node)
		level=LEVEL2
		# Agg to Core links
		for s_index in range(Switch.no_level_1_switches):##s_index start from0
			start_index_of_core_switches=(s_index%Switch.no_of_switches_per_pod)
			for i in range(self.k//2):
				start_node=s_index+Switch.no_level_0_switches
				end_node=start_index_of_core_switches*self.k//2+Switch.no_level_0_switches+Switch.no_level_1_switches+i
				weight=links_parameters["Weight_Links_in_Level_list"][LEVEL2]
				BW=links_parameters["BW_Links_in_Level_list"][LEVEL2]
				#Down direction
				links_index+=1
				name='L'+str(links_index)
				link=Link(name,level,end_node,start_node,weight,BW)
				self.graph.add_edge(end_node,start_node,name=name,weight=weight,BW=BW,BW_with_sup=link.bandwidth_with_ovs)
				links_dict[(end_node,start_node)]=link
				Link.mapping[(start_node,end_node)]=(end_node,start_node)
				Link.mapping[(end_node,start_node)]=(end_node,start_node)

		if len(links_dict)!=Link.number_of_links:
			print ("Error in number of links")
			exit()
		return links_dict

	def build_hosts(self,hosts_parameters):
		#####Hosts
		hosts_list=[]
		Host.host_parameters=hosts_parameters
		####Number of hosts =k^3/4
		Host.no_of_hosts=(self.k**3)//4
		###Number of hosts /switch=k/2
		Host.no_of_hosts_per_switch=self.k//2
		####Traffic rate   #####move to scanario
		Host.max_traffic_rate=hosts_parameters["host_max_traffic_rate"]
		Host.traffic_rate_mean=hosts_parameters["host_flow_rate_mean_per"] * Host.max_traffic_rate   	
		Host.traffic_rate_stdev=hosts_parameters["host_flow_rate_stdev_per"] * Host.max_traffic_rate

		for host_index in range(Host.no_of_hosts):

			parent_switches=[[] for x in range(NUMBER_OF_LEVELS)]
			name='h'+str(host_index)
			pod_index=host_index//(Host.no_of_hosts_per_switch*Switch.no_of_switches_per_pod)
			TOR_switch_index=host_index//(self.k//2)
			agg_switches=list(self.graph.neighbors(TOR_switch_index))
			parent_switches[LEVEL0]=[TOR_switch_index]
			parent_switches[LEVEL1]=agg_switches
			parent_switches[LEVEL2]=Switch.switches_list_in_level[LEVEL2]
			ECMP_traffic_descending_routes=[]
			for switch in Switch.switches_list_in_level[LEVEL2]:
				#shortest_path and not all-shortest_paths also weight or method is not a concern 
				# since descending paths are determenstic at this point
				route=shortest_path(self.graph,switch,TOR_switch_index)
				ECMP_traffic_descending_routes.append(route)
				
			host=Host(name,host_index,pod_index,TOR_switch_index,agg_switches,parent_switches,ECMP_traffic_descending_routes)
			hosts_list.append(host)

		if len(hosts_list)!=Host.no_of_hosts:
			print ("Error in number of hosts")
			exit()

		return hosts_list
	

	def __init__(self,Fat_tree_parameters,switches_parameters,links_parameters,hosts_parameters,files_parameters,trace):

		self.files_path=files_parameters["path"]
		self.file=self.files_path+"Tree.txt"
		self.trace=trace
		###########################################Fat tree parameters   initlaization
		#tree
		self.k=Fat_tree_parameters["k"]
		#pod
		self.no_of_pods=self.k
		#Graph
		self.graph=nx.OrderedGraph()  
		#####Switches
		self.switches_list=self.build_switches(switches_parameters)
		#####Links
		self.links_dict=self.build_links(links_parameters)
		#####Hosts
		self.hosts_list=self.build_hosts(hosts_parameters)
		#####################################################################################
		##Fat tree
		add_to_file(self,'w',
			"k="+str(self.k)+"\n#pods="+str(self.no_of_pods)+"\n#Sw/pod="
			+str(Switch.no_of_switches_per_pod),self.trace,False)
		###switches
		add_to_file(self,'a',
			"\n\nSwitches\n Input switches_parameters="+str(Switch.switch_parameters)
			+"\n #L0_SW="+str(Switch.no_level_0_switches)+" "+str(Switch.switches_list_in_level[LEVEL0])
			+"\n #L1_SW="+str(Switch.no_level_1_switches)+" "+str(Switch.switches_list_in_level[LEVEL1])
			+"\n #L2_SW="+str(Switch.no_level_2_switches)+" "+str(Switch.switches_list_in_level[LEVEL2])
			+"\n Res/SW in level 0="+str(Switch.capacity_of_switches_in_level_0_new)
			+"\n SW_capacity_mode="+str(Switch.capacity_mode)+"\n switchs attributes"
			+str(list(self.graph.nodes.data())),self.trace,False)
		#Hosts
		add_to_file(self,'a',
			"\n\nHosts\n #H/SW="+str(Host.no_of_hosts_per_switch)+"\n #H="+str(Host.no_of_hosts)+"\n parameters="+str(Host.host_parameters)
			+"\n hosts attributes="+str([x.__dict__ for x in self.hosts_list]),self.trace,False)
		#links
		add_to_file(self,'a',
			"\n\nLinks\n links_parameters="+str(Link.parameters)
			+"\n #links="+str(Link.number_of_links)
    		+"\n oversubscription_ratio="+str(Link.oversubscription_ratio)
			+"\n links attributes"+json.dumps(list(self.graph.edges.items()), indent = 2),self.trace,False)



if __name__ == '__main__':

	########### Fat tree Architecture
	### Links
	##levels 0 for HOSTS-TOR links
	##Level 1 for TOR -Aggregation links
	##Level 2 for Aggregation-core  links
	###nodes
	##level-1 hosts
	##level0 TOR switches
	##Level1 Aggregation switches
	##Level2 Core swicthes
	#####writing_mode='w' or 'a'====> w mean erase old files while 'a' mean extend  already exist files
	#tree_files={"files_path":"Result/","file_name":"Tree.txt"}
	files={"path":"Result/"}
	Fat_tree={"k":6}
	switches={"rack_capacity":100,"capacity_mode":"VARIABLE"}
	links={"Oversubscription":1.5,"BW_Links_in_Level_list":[100,100,100],"Weight_Links_in_Level_list":[1,1,2]}
	#Hint host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1] for links between TOR and agg
	hosts={"host_max_traffic_rate":links["BW_Links_in_Level_list"][LEVEL1],"host_flow_rate_mean_per":0.5,"host_flow_rate_stdev_per":0.1}
	T=FatTree(Fat_tree_parameters=Fat_tree,switches_parameters=switches,links_parameters=links,hosts_parameters=hosts,files_parameters=files,trace=True)
	#print (T.tree_graph.edges(0,8))
	#print [p for p in all_shortest_paths(T.G2,'S16','S17')]
	#print (vars(T))
	#print (find_switches_in_pod_in_level(2,0))
	#for s in T.hosts_list:
	#	print (s.index,s.TOR_switch_index)
		#print 
	print ("ok")
	
	#print (Switch.capacity_of_switches_in_level_0_new)
	#import sys
	#print(sys.version)
	#print (str(nx.__version__))
#    print [T.x for x in dir(T)]
	#print (str([x.__dict__ for x in T.links_dict]))
