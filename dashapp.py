from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from dash.exceptions import PreventUpdate

# Load the JSON data
with open('fitbit_data_partial_1.json', 'r') as file:
    data = json.load(file)

# Initialize the Dash app
app = Dash(__name__)

# App layout
app.layout = html.Div([
    dcc.Dropdown(
        id='user-selector',
        options=[{'label': user, 'value': user} for user in data.keys()],
        value=list(data.keys())[0],  # Default to the first user
        multi=False,
    ),
    dcc.Graph(id='gantt-chart'),  # Graph for displaying the unified Gantt chart
    dcc.Graph(id='daily-data-chart'),  # Placeholder for the bar chart
])

@app.callback(
    Output('gantt-chart', 'figure'),
    [Input('user-selector', 'value')]
)

def update_chart(selected_user):
    fig = go.Figure()

    if selected_user in data:
        user_data = data[selected_user]
        sensor_names = [key for key in user_data.keys() if key not in ['official_start_date', 'official_end_date']]
        y_positions = list(range(len(sensor_names) * 10, 0, -10))  # Adjusted to use sensor_names

        fig.update_xaxes(
            title='Date',
            type='date',
            dtick="M1",  # Monthly ticks
            tickformat="%b\n%Y",  # Abbreviated month name and full year
            gridcolor='LightGrey'
        )

        fig.update_yaxes(
            title='Sensors',
            tickvals=y_positions,
            ticktext=sensor_names,
            gridcolor='LightGrey',
            type='category'
        )

        # Add dummy traces for legend entries
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                                 marker=dict(color='red', size=8, symbol='x'),
                                 name='Absent Data Day'))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                                 marker=dict(color='orange', size=8),
                                 name='Void Data Day'))
        
        # Check and add official start and end dates as vertical lines
        if 'official_start_date' in user_data and 'official_end_date' in user_data:
            official_start_date = user_data['official_start_date']
            official_end_date = user_data['official_end_date']

            # Add vertical line for official start date
            fig.add_shape(type="line",
                          x0=official_start_date, y0=-1, x1=official_start_date, y1=10,
                          line=dict(color="black", width=2))

            # Add vertical line for official end date
            fig.add_shape(type="line",
                          x0=official_end_date, y0=-1, x1=official_end_date, y1=10,
                          line=dict(color="black", width=2))

        for y, sensor in zip(y_positions, sensor_names):
            sensor_data = user_data[sensor]
            start_date = datetime.strptime(sensor_data['data_start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(sensor_data['data_end_date'], '%Y-%m-%d')
            current_date = start_date

            # Plot active day markers
            while current_date <= end_date:
                str_current_date = current_date.strftime('%Y-%m-%d')
                if str_current_date not in sensor_data['void_data_days'] and str_current_date not in sensor_data['absent_data_days']:
                    hover_text = f"{sensor}: {str_current_date}"  # Hover text showing sensor and date
                    # Adding customdata that contains sensor name and date
                    custom_data = [sensor, str_current_date]
                    fig.add_trace(go.Scatter(
                        x=[current_date],
                        y=[y],
                        mode='markers',
                        marker=dict(color='lightgreen', size=8),
                        showlegend=False,
                        text=hover_text,
                        hoverinfo='text',
                        customdata=[custom_data]  # Assigning custom data here
                    ))
                current_date += timedelta(days=1)

            # Overlay void data days with markers
            for void_day in sensor_data['void_data_days']:
                void_date = datetime.strptime(void_day, '%Y-%m-%d')
                hover_text = f"{sensor}: {str_current_date}"
                fig.add_trace(go.Scatter(
                    x=[void_date],
                    y=[y],
                    mode='markers',
                    marker=dict(color='orange', size=8),
                    showlegend=False,
                    text=hover_text,  # Set the custom hover text here
                    hoverinfo='text'  # Display only the custom text on hover
                ))

            # Overlay absent data days with markers
            for absent_day in sensor_data['absent_data_days']:
                absent_date = datetime.strptime(absent_day, '%Y-%m-%d')
                hover_text = f"{sensor}: {str_current_date}"
                fig.add_trace(go.Scatter(
                    x=[absent_date],
                    y=[y],
                    mode='markers',
                    marker=dict(color='red', size=8, symbol='x'),
                    showlegend=False,
                    text=hover_text,  # Set the custom hover text here
                    hoverinfo='text'  # Display only the custom text on hover
                ))

    fig.update_layout(
        title=f'Sensor Activity for {selected_user}',
        xaxis=dict(title='Date', type='date', dtick="M1", tickformat="%b\n%Y", gridcolor='LightGrey'),
        yaxis=dict(title='Sensors', tickvals=y_positions, ticktext=sensor_names, gridcolor='LightGrey'),
        barmode='overlay',
        height=700
    )

    return fig

@app.callback(
    Output('daily-data-chart', 'figure'),
    [Input('gantt-chart', 'clickData'),
     Input('user-selector', 'value')]
)
def display_click_data(clickData, selected_user):
    # In your callback function for displaying click data
    if clickData is None or selected_user not in data:
        raise PreventUpdate

    clicked_point = clickData['points'][0]
    clicked_date = clicked_point['x']
    selected_sensor = clicked_point['customdata'][0]  # Direct extraction

    # Retrieve the aggregated data for the selected sensor and date
    sensor_data = data[selected_user][selected_sensor].get('aggregated_data', {})
    day_data = sensor_data.get(clicked_date, [])
    
    if not day_data:
        raise PreventUpdate

    # Generate bar chart for the day's data
    fig = go.Figure(data=[
        go.Bar(
            x=[str(hour_data['hour']) for hour_data in day_data],  # Ensure hours are treated as categorical
            y=[hour_data['value'] for hour_data in day_data],
            text=[hour_data['value'] for hour_data in day_data],
            textposition='auto',
        )
    ])

    fig.update_layout(
        title=f'{selected_sensor} Data for {clicked_date}',
        xaxis_title='Hour of the Day',
        yaxis_title='Value',
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
