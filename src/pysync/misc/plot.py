'''
Contains functions for plotting time series data
'''

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time 

def plot_series_data(in_path:str = '1hrfinal.csv', out_path:str = None):
    '''
    Plots the series data saved from the endpoint tester class

    in_path: path to the .csv containing the series data
    out_path: (optional) path to where the plot should be saved
    '''
    try:
        df = pd.read_csv(in_path)
    except FileNotFoundError:
        print(f'Could not find file {in_path}')
        return

    endpoint_cols = [col for col in df.columns if col not in ['iteration', 'approx_runtime']]

    df[endpoint_cols] = df[endpoint_cols]*1000 # convert to ms for y axis

    fig = px.line(
        df, 
        x="approx_runtime",  
        y=endpoint_cols,
        #title="Endpoint Error Over Time",
        labels={
            "approx_runtime": "Experiment Runtime (s)",
            "value": 'Error (ms)',
            "variable": "Endpoint Type"
        },
        template="plotly_white" 
    )

    fig.update_traces(mode="lines+markers", marker=dict(size=4)) 
    fig.update_layout(
        hovermode="x unified", 
        xaxis=dict(showgrid=True, zeroline=True),
        yaxis=dict(showgrid=True, zeroline=True)
    )

    if not out_path:
        fig.show()
        time.sleep(5)
    else:
        # Save light mode graph
        fig.write_image(f"{out_path}/graph-light.png")
        fig.update_layout(template="plotly_dark")
        fig.write_image(f"{out_path}/graph-dark.png")


if __name__ == '__main__':
    #plot_series_data()
    plot_series_data(in_path='assets/1hrfinal.csv',out_path='assets')