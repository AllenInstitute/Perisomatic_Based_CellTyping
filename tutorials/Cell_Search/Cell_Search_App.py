import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.express as px
import utils
import pyperclip


# Load the UMAP data
data_path = '../../data/microns_SomaData_AllCells_v661.pkl'
umap_data = pd.read_pickle(data_path)

empty_neuroglancer_link = utils.get_neuroglancer_link()

# Ensure the required columns exist in the data
if 'umap_embedding_x' not in umap_data.columns or 'umap_embedding_y' not in umap_data.columns:
    raise ValueError("The UMAP data must contain 'umap_embedding_x' and 'umap_embedding_y' columns.")

# Create a default UMAP scatter plot
default_scatter_fig = px.scatter(
    umap_data,
    x='umap_embedding_x',
    y='umap_embedding_y',
    #title="UMAP Projection of Cells",
    labels={'umap_embedding_x': 'UMAP X', 'umap_embedding_y': 'UMAP Y'},
    color='predicted_subclass',
    template='plotly_white',
    hover_data = {
    'predicted_class': True,
    'predicted_subclass': True,
    'umap_embedding_x': False,
    'umap_embedding_y': False
    }
)
# Update default scatter plot appearance
default_scatter_fig.update_traces(marker=dict(size=2, opacity=0.4))  # Smaller gray points
default_scatter_fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)  # Remove grid

#Will be an empty plot placeholder for the neighbor distance plot
default_neighbor_fig = px.scatter(
    x=[0],
    y=[0]
)
default_neighbor_fig.update_traces(marker=dict(size=2, opacity=0.0))  # Smaller gray points
default_neighbor_fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)  # Remove grid

# Initialize the Dash app
app = dash.Dash(__name__,prevent_initial_callbacks = True)

# Load external CSS for styling
app.css.append_css({
    "external_url": "/assets/dash_style.css"
})

# Add a title and subtitle to the app
app.title = "Cell Search App"


# Define the layout of the app
app.layout = html.Div(
    style={'display': 'flex', 'flexDirection': 'column', 'height': '100vh'},
    children=[
        # Header
        html.Div(
            style={'textAlign': 'center', 'padding': '20px', 'borderBottom': '1px solid #ccc', 'width': '100%'},
            children=[
                html.H1("Cell Search App"),
                html.H3("Looking for more cells? This app helps you find other cells in the MICrONS dataset that have similar perisomatic features to your cell of interest.")
            ]
        ),
        # Main content: Left and Right windows
        html.Div(
            style={'display': 'flex', 'height': '300vh'},
            children=[
                # Left window: Input box and dropdown menu
                html.Div(
                    style={'flex': '1', 'padding': '20px', 'borderRight': '1px solid #ccc'},
                    children=[
                        html.H4("1. What cell are you interested in?"),
                        html.P("Enter the cell ID and select the type of ID you have."),
                        dcc.Input(
                            id='cell-id-input',
                            type='text',
                            placeholder='Enter Cell ID',
                            style={'width': '100%', 'marginBottom': '10px'}
                        ),
                        dcc.Dropdown(
                            id='id-type-dropdown',
                            options=[
                                {'label': 'Nucleus ID', 'value': 'nucleus_id'},
                                 {'label': 'Segment ID', 'value': 'seg_id'}
                            ],
                            placeholder='Select ID Type',
                            style={'width': '100%'}
                        ),
                        html.Button(
                            'Find My Cell',
                            id='search-button',
                            style={'width': '50%', 'marginTop': '10px'}
                        ),
                        html.Button(
                            'Reset',
                            id='reset-button',
                            style={'width': '30%', 'marginTop': '10px'}
                        ),
                        html.H4("2. How many similar cells would you like to see?"),
                        dcc.Input(
                            id='neighbor-id-input',
                            type='text',
                            placeholder='Enter the number of similar cells you would like to search for',
                            style={'width': '100%', 'marginBottom': '10px'}
                        ),
                        html.Button(
                            'Find More Cells!',
                            id='neighbor-button',
                            style={'width': '33%','marginTop': '10px'}
                        ),
                        html.Button(
                            'Copy Cell IDs',
                            id='copy-button',
                            style={'width': '33%', 'marginTop': '10px'}
                        ),
                    
                        html.A(
                            html.Button(
                                'Open Neuroglancer',
                                id='neuroglancer-link-button',
                                style={'width': '33%', 'marginTop': '10px'}
                            ),
                            href=empty_neuroglancer_link,
                            id='neuroglancer-button-link',
                            target='_blank'
                        ),
                        dcc.Graph(figure=default_neighbor_fig, 
                                  id='default-neighbor-plot',
                                  style={'display': 'none'})  # Initially hidden,
                    ]
                ),
                # Right window: Default scatter plot
                html.Div(
                    style={'height': '500px', 'width': '400px', 'flex': '2', 'padding': '20px'},
                    children=[
                        html.H4("Interactive UMAP with predicted cell-types"),
                        dcc.Graph(figure=default_scatter_fig, id='default-scatter-plot'),
                        html.Div(id='output-content', style={'marginTop': '20px'})
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    [Output('default-scatter-plot', 'figure'),
    Output('default-neighbor-plot', 'figure')],
    [Input('search-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [dash.dependencies.State('cell-id-input', 'value'),
     dash.dependencies.State('id-type-dropdown', 'value')]
)
def highlight_cell(search_clicks, reset_clicks, cell_id, id_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        return default_scatter_fig

    if id_type == 'seg_id':
        cell_id = utils.get_nuc_id_from_seg_id(cell_id)

        
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'reset-button':
        return default_scatter_fig, default_neighbor_fig

    if triggered_id == 'search-button' and cell_id:
        # Copy the data to avoid modifying the original dataframe
        plot_data = umap_data.copy()
        cell_id = int(cell_id)
        seg_ids = [cell_id]
        # Add a new column for marker size and color
        plot_data['marker_size'] = 2
        plot_data['marker_color'] = 'lightgray'
        plot_data['marker_opacity'] = 0.4

        # Highlight the cell of interest
        plot_data.loc[plot_data['nucleus_id'] == cell_id, 'marker_size'] = 10
        plot_data.loc[plot_data['nucleus_id'] == cell_id, 'marker_color'] = 'orange'
        plot_data.loc[plot_data['nucleus_id'] == cell_id, 'marker_opacity'] = 1.0
        print(plot_data.loc[plot_data['nucleus_id'] == cell_id].predicted_subclass.values[0])
        plot_data = plot_data.sort_values(by='marker_size', ascending=True)
        # Create the updated scatter plot
        scatter_fig = px.scatter(
            plot_data,
            x='umap_embedding_x',
            y='umap_embedding_y',
            title="Cell of Interest within the Dataset",
            labels={'umap_embedding_x': 'UMAP X', 'umap_embedding_y': 'UMAP Y'},
            template='plotly_white',
            hover_data={
                'predicted_class': True,
                'predicted_subclass': True,
                'umap_embedding_x': False,
                'umap_embedding_y': False
            }
        )
        scatter_fig.update_traces(marker=dict(
                size=plot_data['marker_size'],
                color=plot_data['marker_color'],
                opacity=plot_data['marker_opacity'],
                line=dict(width=0)
            ))
        scatter_fig.update_layout(height=600, xaxis_showgrid=False, yaxis_showgrid=False)

        return scatter_fig, default_neighbor_fig

    # Return the default scatter plot if no valid interaction
    return default_scatter_fig, default_neighbor_fig


@app.callback(
    Output('default-scatter-plot', 'figure', allow_duplicate=True),
    Output('default-neighbor-plot', 'figure', allow_duplicate=True),
    Output(component_id='default-neighbor-plot', component_property='style'),
    [Input('neighbor-button', 'n_clicks'),
     Input('copy-button', 'n_clicks')],
    [dash.dependencies.State('cell-id-input', 'value'),
     dash.dependencies.State('neighbor-id-input', 'value'),
     dash.dependencies.State('id-type-dropdown', 'value')],
    prevent_initial_call=True
)
def handle_neighbor_and_copy(neighbor_clicks, copy_clicks, cell_id, n_neighbors, id_type):
    ctx = dash.callback_context
    if not ctx.triggered:
        return default_scatter_fig, default_neighbor_fig, {'display': 'none'}
    
    if id_type == 'seg_id':
        cell_id = utils.get_nuc_id_from_seg_id(cell_id)

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'neighbor-button' and neighbor_clicks and n_neighbors and n_neighbors.isdigit():
        n_neighbors = int(n_neighbors)
        # Copy the data to avoid modifying the original dataframe
        plot_data = umap_data.copy()
        # Call the find_nearest_neighbors function
        nuc_neighbors, soma_neighbors, all_distances = utils.find_nearest_neighbors(df=plot_data, cell_id=cell_id, feature_set='soma_metrics', n_neighbors=n_neighbors)
        cell_id = nuc_neighbors[0]
        nuc_neighbors = nuc_neighbors[1:]

        seg_ids = soma_neighbors
        # Add a new column for marker size and color
        plot_data['marker_size'] = 2
        plot_data['marker_color'] = 'lightgray'
        plot_data['marker_opacity'] = 0.4

        # Highlight the nearest neighbors
        plot_data.loc[plot_data.nucleus_id.isin(nuc_neighbors), 'marker_size'] = 5
        plot_data.loc[plot_data.nucleus_id.isin(nuc_neighbors), 'marker_color'] = 'teal'
        plot_data.loc[plot_data.nucleus_id.isin(nuc_neighbors), 'marker_opacity'] = 1.0

        # Highlight the cell of interest
        plot_data.loc[plot_data['nucleus_id'] == cell_id, 'marker_size'] = 10
        plot_data.loc[plot_data['nucleus_id'] == cell_id, 'marker_color'] = 'orange'
        plot_data.loc[plot_data['nucleus_id'] == cell_id, 'marker_opacity'] = 1.0

        plot_data = plot_data.sort_values(by='marker_size', ascending=True)
        # Create the updated scatter plot
        scatter_fig = px.scatter(
            plot_data,
            x='umap_embedding_x',
            y='umap_embedding_y',
            title=f"{len(nuc_neighbors)} Nearest Neighbors to your Cell of Interest",
            labels={'umap_embedding_x': 'UMAP X', 'umap_embedding_y': 'UMAP Y'},
            template='plotly_white',
            hover_data={
                'predicted_class': True,
                'predicted_subclass': True,
                'umap_embedding_x': False,
                'umap_embedding_y': False
            }
        )
        scatter_fig.update_traces(marker=dict(
                size=plot_data['marker_size'],
                color=plot_data['marker_color'],
                opacity=plot_data['marker_opacity'],
                line=dict(width=0)
            ))
        scatter_fig.update_layout(height=500, xaxis_showgrid=False, yaxis_showgrid=False)

        # Create the neighbor distance plot
        n_neighbors = int(n_neighbors)
        # Create a color list for the neighbors
        left = len(all_distances) - n_neighbors - 1
        neighbor_colors = ['orange'] + (['teal'] * n_neighbors) + (['lightgray'] * left)
        # Generate the neighbor distance figure
        neighbor_distance_fig = px.scatter(
            x=np.arange(len(all_distances)),
            y=all_distances,
            title="Distance to Nearest Neighbors",
            labels={'x': 'Neighbor Index', 'y': 'Distance'},
            template='plotly_white',
            log_x=True,
            log_y=True
        )
        
        neighbor_distance_fig.update_layout(height=300,width=500, xaxis_showgrid=False, yaxis_showgrid=False)
        neighbor_distance_fig.update_traces(marker=dict(
                color=neighbor_colors))

        visibility = {'display': 'block'}
        return scatter_fig, neighbor_distance_fig, visibility

    elif triggered_id == 'copy-button' and copy_clicks and n_neighbors and n_neighbors.isdigit():
        n_neighbors = int(n_neighbors)
        # Call the find_nearest_neighbors function
        plot_data = umap_data.copy()
        nuc_neighbors, soma_neighbors, all_distances = utils.find_nearest_neighbors(df=plot_data, 
                                                                              cell_id=cell_id, 
                                                                              feature_set='soma_metrics', 
                                                                              n_neighbors=n_neighbors)
        # Copy the soma_neighbors to clipboard
        seg_ids = utils.get_latest_seg_ids(nuc_neighbors)
        pyperclip.copy(', '.join(map(str, seg_ids)))
        return dash.no_update, dash.no_update, dash.no_update

    visibility = {'display': 'none'}
    seg_ids = []
    # Return the default scatter plots and hide neighbor_fig if no valid interaction
    return default_scatter_fig, default_neighbor_fig, visibility


@app.callback(
    Output('neuroglancer-button-link', 'href'),
    [Input('neuroglancer-link-button', 'n_clicks')],
    [dash.dependencies.State('cell-id-input', 'value'),
    dash.dependencies.State('neighbor-id-input', 'value'),
     dash.dependencies.State('id-type-dropdown', 'value')],
    prevent_initial_call=True
)
def open_neuroglancer(neuroglancer_clicks, cell_id, n_neighbors, id_type):
    ctx = dash.callback_context
 
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(neuroglancer_clicks)
    if triggered_id == 'neuroglancer-link-button' and cell_id and n_neighbors:
        print('passed conditional!')
        if id_type == 'seg_id':
            cell_id = utils.get_nuc_id_from_seg_id(cell_id)

        n_neighbors = int(n_neighbors)
        plot_data = umap_data.copy()
        nuc_neighbors, soma_neighbors, all_distances = utils.find_nearest_neighbors(df=plot_data, 
                                                                              cell_id=cell_id, 
                                                                              feature_set='soma_metrics', 
                                                                              n_neighbors=n_neighbors)
        seg_ids = utils.get_latest_seg_ids(nuc_neighbors)

        return utils.get_neuroglancer_link(segment_ids=seg_ids)
    
    elif triggered_id == 'neuroglancer-link-button':
        return empty_neuroglancer_link
    
    return dash.no_update
# Run the app
if __name__ == '__main__':
    app.run(debug=True)
    

    