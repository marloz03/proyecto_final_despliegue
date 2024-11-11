#!/usr/bin/env python
# coding: utf-8

# In[1]:


from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# Cargar el dataset
df = pd.read_csv('dataset.csv', parse_dates=['trans_date_trans_time'])

# Crear las columnas necesarias una vez para evitar modificaciones dentro de los callbacks
df['date'] = df['trans_date_trans_time'].dt.date
df['hour'] = df['trans_date_trans_time'].dt.hour
df['day_of_week'] = df['trans_date_trans_time'].dt.day_name()  # Día de la semana
df['month'] = df['trans_date_trans_time'].dt.month

# Crear etiquetas de franjas horarias
hour_labels = [f"{str(i).zfill(2)}:00 - {str(i+1).zfill(2)}:00" for i in range(24)]
days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Obtener la lista de estados y categorías únicos para los filtros
states = ['Todos'] + sorted(df['state'].dropna().unique().tolist())
categories = ['Todas'] + sorted(df['category'].dropna().unique().tolist())
months = ['Todos'] + sorted(df['month'].unique().tolist())

# Inicializar la aplicación
app = Dash(__name__)

# Crear el layout de la aplicación
app.layout = html.Div(style={'backgroundColor': '#1f2630', 'color': 'white', 'padding': '10px', 'font-family': 'Arial', 'font-size': '24px'}, children=[
    html.H1('Análisis de Transacciones Fraudulentas en Estados Unidos', style={'textAlign': 'center', 'color': '#9bb8b7'}),

    # Filtros
    html.Div([
        html.Div([
            html.Label('Selecciona el estado:', style={'color': 'white', 'font-size': '14px'}),
            dcc.Dropdown(
                id='state-filter',
                options=[{'label': state, 'value': state} for state in states],
                value='Todos',
                style={'width': '100%', 'color': 'black', 'backgroundColor': 'white'}
            ),
        ], style={'padding': '10px', 'width': '32%', 'display': 'inline-block'}),
        
        html.Div([
            html.Label('Selecciona la categoría:', style={'color': 'white', 'font-size': '14px'}),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': category, 'value': category} for category in categories],
                value='Todas',
                style={'width': '100%', 'color': 'black', 'backgroundColor': 'white'}
            ),
        ], style={'padding': '10px', 'width': '32%', 'display': 'inline-block'}),

        html.Div([
            html.Label('Selecciona el mes:', style={'color': 'white', 'font-size': '14px'}),
            dcc.Dropdown(
                id='month-filter',
                options=[{'label': month, 'value': month} for month in months],
                value='Todos',
                style={'width': '100%', 'color': 'black', 'backgroundColor': 'white'}
            ),
        ], style={'padding': '10px', 'width': '32%', 'display': 'inline-block'}),
    ]),

    # Primer gráfico: Mapa de Calor de Transacciones Fraude
    html.Div([
        html.H3('Mapa de Calor de Transacciones Fraude', style={'color': '#9bb8b7'}),
        dcc.Graph(id='heatmap', style={'height': '500px'})
    ], style={'width': '100%', 'padding': '10px'}),

    # Gráficos en una sola fila
    html.Div([
        html.Div([
            html.H3('Distribución de Género', style={'color': '#9bb8b7'}),
            dcc.Graph(id='gender-distribution', style={'height': '400px'})
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),

        html.Div([
            html.H3('Distribución de Categorías de Transacción', style={'color': '#9bb8b7'}),
            dcc.Graph(id='category-distribution', style={'height': '400px'})
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),

        html.Div([
            html.H3('Transacciones Fraude por Mercado', style={'color': '#9bb8b7'}),
            dcc.Graph(id='merchant-distribution', style={'height': '400px'})
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between'}),

    # Último gráfico: Interacción por Franja Horaria y Día de la Semana
    html.Div([
        html.H3('Interacción por Franja Horaria y Día de la Semana', style={'color': '#9bb8b7', 'textAlign': 'center'}),
        dcc.Graph(id='weekly-hourly-frequency', style={'height': '800px', 'width': '100%', 'margin': '0 auto', 'display': 'block'})
    ], style={'padding': '10px', 'textAlign': 'center'})
])

# Definir los callbacks para actualizar cada gráfico con estilo oscuro y los filtros
@app.callback(
    Output('heatmap', 'figure'),
    [Input('heatmap', 'id'), Input('state-filter', 'value'), Input('category-filter', 'value'), Input('month-filter', 'value')]
)
def update_heatmap(_, selected_state, selected_category, selected_month):
    filtered_df = df
    if selected_state != 'Todos':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_category != 'Todas':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_month != 'Todos':
        filtered_df = filtered_df[filtered_df['month'] == int(selected_month)]
    
    fig = px.density_mapbox(
        filtered_df, lat='lat', lon='long', z='amt', radius=10,
        center=dict(lat=37.0902, lon=-95.7129),
        zoom=4,
        mapbox_style="carto-darkmatter"
    )
    fig.update_layout(paper_bgcolor='#1f2630', font_color='white')
    return fig

@app.callback(
    Output('gender-distribution', 'figure'),
    [Input('state-filter', 'value'), Input('category-filter', 'value'), Input('month-filter', 'value')]
)
def update_gender_distribution(selected_state, selected_category, selected_month):
    filtered_df = df
    if selected_state != 'Todos':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_category != 'Todas':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_month != 'Todos':
        filtered_df = filtered_df[filtered_df['month'] == int(selected_month)]

    fig = px.pie(filtered_df, names='gender')
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(paper_bgcolor='#1f2630', font_color='white')
    return fig

@app.callback(
    Output('category-distribution', 'figure'),
    [Input('state-filter', 'value'), Input('category-filter', 'value'), Input('month-filter', 'value')]
)
def update_category_distribution(selected_state, selected_category, selected_month):
    filtered_df = df
    if selected_state != 'Todos':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_category != 'Todas':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_month != 'Todos':
        filtered_df = filtered_df[filtered_df['month'] == int(selected_month)]

    fig = px.histogram(filtered_df, x='category', color='category', color_discrete_sequence=px.colors.sequential.Viridis)
    fig.update_layout(paper_bgcolor='#1f2630', plot_bgcolor='#1f2630', font_color='white')
    return fig

@app.callback(
    Output('merchant-distribution', 'figure'),
    Input('state-filter', 'value')
)
def update_merchant_distribution(selected_state):
    filtered_df = df[df['is_fraud'] == 1]
    if selected_state != 'Todos':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]

    fig = px.histogram(filtered_df, x='merchant', color='merchant', color_discrete_sequence=px.colors.sequential.Viridis)
    fig.update_layout(paper_bgcolor='#1f2630', plot_bgcolor='#1f2630', font_color='white')
    return fig

@app.callback(
    Output('weekly-hourly-frequency', 'figure'),
    [Input('state-filter', 'value'), Input('category-filter', 'value'), Input('month-filter', 'value')]
)
def update_weekly_hourly_frequency(selected_state, selected_category, selected_month):
    filtered_df = df
    if selected_state != 'Todos':
        filtered_df = filtered_df[filtered_df['state'] == selected_state]
    if selected_category != 'Todas':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_month != 'Todos':
        filtered_df = filtered_df[filtered_df['month'] == int(selected_month)]
    
    heatmap_data = (
        filtered_df
        .groupby(['hour', 'day_of_week'])
        .size()
        .unstack(fill_value=0)
        .reindex(range(24), fill_value=0)
        .reindex(columns=days_order, fill_value=0)
    )

    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Día de la Semana", y="Franja Horaria", color="Cantidad de Transacciones"),
        x=days_order,
        y=hour_labels,
        color_continuous_scale=px.colors.sequential.Oranges,
        zmin=0,
        zmax=10000,
        aspect="auto"
    )
    fig.update_layout(
        paper_bgcolor='#1f2630', 
        font_color='white',
        height=800,
        width=1500,
        xaxis=dict(tickangle=45),
        yaxis_nticks=24
    )
    return fig

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, port=8020)


# In[ ]:




