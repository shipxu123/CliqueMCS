import os
import json
import networkx as nx
# from isign_mcs.algorithms import getMCS_VF2, getMCS_HM

from networkx.readwrite import json_graph

import pdb

import subprocess

def find_maxclique(match_graph_file, algorithm):
    output = subprocess.check_output(['/home/pxu/codes/CliqueMCS/open-mcs/bin/open-mcs', f'--input-file={match_graph_file}', \
                                    f'--algorithm={algorithm}']).decode('utf-8')

    return [int(i) for i in str(output).split('\n')[-2].split()]

def getMCS(target_path, query_path):
    with open(target_path, "rb") as f:
        Gt = json_graph.node_link_graph(json.load(f))

    with open(query_path, "rb") as f:
        Gq = json_graph.node_link_graph(json.load(f))

    def node_match(node1, node2):
        if 'inst_type' in node1 and 'inst_type' in node2:
            if node1['inst_type'] == node2['inst_type']:
                return True

        return False

    def edge_match(edge1, edge2):
        is_valid = (edge1['weight'] == edge2['weight'])
        return is_valid

    matching_map   =  {}
    matching_graph = nx.Graph()

    for v, attr_v in Gq.nodes(data=True):
        for u, attr_u in Gt.nodes(data=True):

            if node_match(attr_v, attr_u):
                matching_graph.add_node(str((v, u)))

                if v not in matching_map:
                    matching_map[v] = set([u])
                else:
                    matching_map[v].add(u)

    for v1, v2, edge_v in Gq.edges(data=True):
        assert(v1 != v2)

        if v1 not in matching_map or v2 not in matching_map:
            continue

        for u1, u2, edge_u in Gt.edges(data=True):
            assert(u1 != u2)

            if u1 in matching_map[v1] and u2 in matching_map[v2]:
                if edge_match(edge_v, edge_u):
                    matching_graph.add_edge(str((v1, u1)), str((v2, u2)))

    Gq_Complete = nx.complement(Gq)
    Gt_Complete = nx.complement(Gt)

    for v1, v2 in Gq_Complete.edges():
        assert(v1 != v2)

        if v1 not in matching_map or v2 not in matching_map:
            continue

        for u1, u2 in Gt_Complete.edges():
            assert(u1 != u2)

            if u1 in matching_map[v1] and u2 in matching_map[v2]:
                matching_graph.add_edge(str((v1, u1)), str((v2, u2)))

    dimacs_filename = f"{target_path.split('/')[-1].split('.')[0]}-{query_path.split('/')[-1].split('.')[0]}.graph.txt"

    matching_indexes = {}

    for i, node in enumerate(matching_graph.nodes()):
        matching_indexes[str(node)] = i

    with open(dimacs_filename, "w") as f:
        # write the header
        # f.write("p EDGE {} {}\n".format(matching_graph.number_of_nodes(), matching_graph.number_of_edges()))
        f.write("{} {}\n".format(matching_graph.number_of_nodes(), matching_graph.number_of_edges()))

        for i, node in enumerate(matching_graph.nodes()):
            for v in matching_graph.adj[node].keys():
                if i != matching_indexes[str(v)]:
                    f.write("{} ".format(matching_indexes[str(v)]))

            f.write("\n")

    matching_nodes = [n for n in matching_graph.nodes()]

    print(f'Processing query graph : {query_path} and target graph : {target_path}')

    # return matching_nodes
    largest_clique = [matching_nodes[i] for i in find_maxclique(dimacs_filename, 'mcs')]
    print(f'Matched Results : {largest_clique}')
    return largest_clique


if __name__ == "__main__":
    query_dir = '/home/pxu/data/ISign_Data/2024_06_11_dac_analog_top/match/bipartite_graph_train_data/graphs'
    target_dir = '/home/pxu/data/ISign_Data/2024_06_11_dac_analog_top/match/bipartite_graph_train_data/graphs'

    # similarity_dict = {}
    mcs_dict = {}

    for query_cir_name in os.listdir(query_dir):
        # similarity_dict[query_cir_name] = {}
        mcs_dict[query_cir_name] = {}

        for target_cir_name in os.listdir(target_dir):
            print(f'Processing query graph : {query_cir_name} and target graph : {target_cir_name}')

            mcs = getMCS(target_path=os.path.join(target_dir, target_cir_name), 
                                              query_path=os.path.join(query_dir, query_cir_name))
            mcs_dict[query_cir_name][target_cir_name] = mcs
            print(mcs)


    # print(similarity)
    print(mcs)
