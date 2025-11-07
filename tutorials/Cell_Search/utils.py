from sklearn.neighbors import KDTree
from sklearn import preprocessing
from nglui import statebuilder
import caveclient

"""
Utility functions for cell search and analysis in connectomics data.
This module provides tools for finding similar cells based on morphological features,
managing cell IDs, and generating visualization links for neuroglancer.
Global Variables:
    client: CAVEclient instance for accessing minnie65_public dataset
    seg_source: Segmentation data source from the client
    img_source: Image data source from the client
    nuc_df: DataFrame containing nucleus detection data with soma information
    soma_metrics: List of morphological feature names for soma analysis
    feature_dict: Dictionary mapping feature set names to feature lists
"""
    
# set client object
client = caveclient.CAVEclient('minnie65_public')
seg_source = client.info.segmentation_source()
img_source = client.info.image_source()

#nucleus table with all cells with a soma within the dataset
nuc_df = client.materialize.query_view('nucleus_detection_lookup_v1', split_positions=True, 
                                       desired_resolution=(1000,1000,1000))

soma_metrics = [ 'soma_depth_y','nucleus_volume_um', 'nucleus_area_um', 
                'nuclear_area_to_volume_ratio', 'nuclear_folding_area_um', 
                'fraction_nuclear_folding', 'nucleus_to_soma_ratio', 
                'soma_volume_um', 'soma_area_um', 'soma_to_nucleus_center_dist', 
                'soma_area_to_volume_ratio', 'soma_synapse_number', 'soma_synapse_density_um']

feature_dict = {'soma_metrics':soma_metrics}

def get_nuc_id_from_seg_id(cell_id):
    """
    Convert a segment ID to its corresponding nucleus ID.
    Args:
        cell_id: Segment ID (pt_root_id) to convert
    Returns:
        int: Nucleus ID if found
        str: Error message if no nucleus found or multiple nuclei found
    """
    seg_id = int(cell_id)
    nuc_id = nuc_df.query('pt_root_id == @seg_id').id.tolist()

    if len(nuc_id) == 0:
        return "Error: No nucleus found. Please use the most recent pt_root_id."
    if len(nuc_id) > 1:
        return "Error: Multiple nuclei found for this pt_root_id. Please refine your input."
  
    cell_id = nuc_id[0]
    return cell_id

def get_latest_seg_ids(nuc_ids):
    """
    Convert nucleus IDs to their corresponding latest segment IDs.
    Args:
        nuc_ids (list): List of nucleus IDs to convert
    Returns:
        list: List of corresponding pt_root_ids (segment IDs)
    """
    updated_ids = []
    for n in nuc_ids:
        seg_id = nuc_df.query('id == @n').pt_root_id.tolist()[0]
        updated_ids.append(seg_id)
    return updated_ids

def find_nearest_neighbors(df, cell_id, feature_set,n_neighbors):
    """
    Find the nearest neighboring cells based on morphological features using KDTree.
    Uses standardized features and Euclidean distance in high-dimensional space
    to identify cells with similar morphological properties.
    Args:
        df (pandas.DataFrame): DataFrame containing cell data with features
        cell_id (int): Nucleus ID of the target cell
        feature_set (str): Key for feature_dict specifying which features to use
        n_neighbors (int): Number of nearest neighbors to return
    Returns:
        tuple: A tuple containing:
            - similar_neuron_nuc_ids (list): Nucleus IDs of similar cells
            - similar_neurons (list): Soma IDs of similar cells  
            - broad_distances (array): Distances to a broader set of neighbors
    """

    df = df.reset_index(drop=True) #reset index to avoid issues with KDTree
    feature_values = feature_dict[feature_set]
    cell_features = df[feature_values].to_numpy() #convert to numpy array

    #Normalize the features
    scaler=preprocessing.StandardScaler().fit(cell_features)
    cell_features_normalized = scaler.transform(cell_features)
    n_features = len(feature_values)
    cell_id = int(cell_id) #convert to int
    
    #KDTree on high dimensional feature space
    kdt = KDTree(cell_features_normalized, leaf_size=30, metric='euclidean')

    #Id of our cell of interest
    print("cell_id", cell_id)
    print("type cell_id", type(cell_id))
    idx = df.query('nucleus_id == @cell_id').index[0]
    print("Index of the cell of interest:", idx, "Cell ID:", cell_id)
    X = cell_features_normalized[idx,:].reshape(1,n_features) #corresponding feature vector for that cell

    n_cells = cell_features_normalized.shape[0]
    #Query for the top 20 nearest neighbors 
    all_distances, all_idxs = kdt.query(X, k=n_cells, return_distance=True)
    broad_distances = all_distances[0][:(n_neighbors*10)+1]
    similar_idxs = all_idxs[0][:n_neighbors+1] #including the first one, which is the cell itself
    print("similar_idxs",similar_idxs)
    similar_neurons = df.soma_id.iloc[similar_idxs].tolist()
    similar_neuron_nuc_ids = df.nucleus_id.iloc[similar_idxs].tolist()
    print("similar neurons",similar_neurons)


    return similar_neuron_nuc_ids, similar_neurons,broad_distances

def get_neuroglancer_link(segment_ids=[]):
    """
    Generate a neuroglancer visualization URL for specified segments.
    Creates a viewer state with image and segmentation layers, highlighting
    the provided segment IDs for visualization.
    Args:
        segment_ids (list, optional): List of segment IDs to highlight. 
                                    Defaults to empty list.
    Returns:
        str: URL for neuroglancer viewer with the specified segments
    """

    viewer_state = (
        statebuilder.ViewerState(dimensions=[4,4,40])
        .add_image_layer(
            source=img_source,
            name='emdata'
        )
        .add_segmentation_layer(
            source=seg_source,
            name='seg',
            segments=segment_ids,
        )

    )
    url = viewer_state.to_url(client=client)
    return url

if __name__ == '__main__':
    print("The utils script is being run directly.")