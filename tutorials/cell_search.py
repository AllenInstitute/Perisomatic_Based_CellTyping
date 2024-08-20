import math
import caveclient
import numpy as np
import pandas as pd
from multiprocessing import Pool

client = caveclient.CAVEclient('minnie65_public')
nuc_df = client.materialize.query_table('nucleus_detection_v0',  
                                       desired_resolution=(1000,1000,1000))
mm_df = client.materialize.query_table('aibs_metamodel_celltypes_v661', desired_resolution=(1000,1000,1000))

def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'"""
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    rad= np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    return rad, math.degrees(rad)

def get_syn_angle(pts):
    soma_pt = pts[0]
    soma_pt = soma_pt[:2]
    
    syn_pt=pts[1]
    syn_pt = syn_pt[:2]
    
    straight_up = straight_up = [soma_pt[0],0]
    pq= straight_up - soma_pt
    pr = syn_pt - soma_pt
    dist = np.abs(pr[1]) #distance in y between soma and synapse
    rads = angle_between(pq,pr)
    rad = rads[0]
    angle = rads[1]
    return dist, rad, angle

def get_syn_out_df(rootid):
    syn_in_df = client.materialize.synapse_query(post_ids=rootid,#timestamp=now, 
                                            #split_positions=True,
                                             desired_resolution=(1000,1000,1000))
    syn_out_df = client.materialize.synapse_query(pre_ids=rootid,#timestamp=now,
                                             #split_positions=True,
                                             desired_resolution=(1000,1000,1000))
    merged_syn_out = syn_out_df.merge(nuc_df[['pt_root_id','pt_position']],how='inner',
                left_on='post_pt_root_id', right_on='pt_root_id')
    
    merged_syn_out = merged_syn_out.merge(mm_df[['pt_root_id','classification_system','cell_type']],how='inner',
                left_on='post_pt_root_id', right_on='pt_root_id')

    merged_syn_out = merged_syn_out.drop_duplicates('id')
    
    return merged_syn_out


def get_angle_df(syn_df):
    pts = list(zip(syn_df.pt_position,syn_df.post_pt_position))
    
    with Pool(5) as p:
        rads_angles = p.map(get_syn_angle, pts)
    
    ydist = [i[0] for i in rads_angles]
    rads = [i[1] for i in rads_angles]
    angles = [i[2] for i in rads_angles]
    angle_df = pd.DataFrame()
    angle_df['pre_pt_root_id'] = syn_df.pre_pt_root_id
    angle_df['post_pt_root_id'] = syn_df.post_pt_root_id
    angle_df['target_ct'] = syn_df.cell_type
    angle_df['target_class'] = syn_df.classification_system
    angle_df['angle_to_post_rad'] = rads
    angle_df['angle_to_post_deg'] = angles
    angle_df['y_dist'] = ydist
    angle_df['size'] = syn_df['size']
    
    return angle_df