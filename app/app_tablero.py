#!/usr/bin/env python
# coding: utf-8

# In[1]:


from dash import Dash, html, dcc, Input, Output, State
from dash.dash_table import DataTable
import plotly.express as px
import pandas as pd
import base64
import os
from prediction import realizar_prediccion

# Inicializar la aplicación
app = Dash(__name__)

# Dataset base
df = pd.read_csv('datos/sample_input.csv', parse_dates=['trans_date_trans_time'], low_memory=False)
df = df.loc[~(df['id'].isna()), :]
df['date'] = df['trans_date_trans_time'].dt.date
df['hour'] = df['trans_date_trans_time'].dt.hour
df['day_of_week'] = df['trans_date_trans_time'].dt.day_name()
df['month'] = df['trans_date_trans_time'].dt.month

hour_labels = [f"{str(i).zfill(2)}:00 - {str(i+1).zfill(2)}:00" for i in range(24)]
days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

states = ['Todos'] + sorted(df['state'].dropna().unique().tolist())
categories = ['Todas'] + sorted(df['category'].dropna().unique().tolist())
months = ['Todos'] + sorted([1,2,3,4,5,6,7,8,9,10,11,12])

# Layout de la aplicación
app.layout = html.Div(style={'backgroundColor': '#1f2630', 'color': 'white', 'padding': '10px'}, children=[
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

    # Gráficos originales
    html.Div([
        html.H3('Mapa de Calor de Transacciones Fraude', style={'color': '#9bb8b7'}),
        dcc.Graph(id='heatmap', style={'height': '500px'}),
    ], style={'width': '100%', 'padding': '10px'}),

    html.Div([
        html.Div([
            html.H3('Distribución de Género', style={'color': '#9bb8b7'}),
            dcc.Graph(id='gender-distribution', style={'height': '400px'}),
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.H3('Distribución de Categorías de Transacción', style={'color': '#9bb8b7'}),
            dcc.Graph(id='category-distribution', style={'height': '400px'}),
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.H3('Transacciones Fraude por Mercado', style={'color': '#9bb8b7'}),
            dcc.Graph(id='merchant-distribution', style={'height': '400px'}),
        ], style={'width': '32%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between'}),

    html.Div([
        html.H3('Interacción por Franja Horaria y Día de la Semana', style={'color': '#9bb8b7'}),
        dcc.Graph(id='weekly-hourly-frequency', style={'height': '800px'}),
    ]),

    # Subida de archivo
    html.Div([
        html.Label('Sube un archivo CSV para procesar predicciones:', style={'color': 'white', 'font-size': '16px'}),
        dcc.Upload(
            id='upload-input',
            children=html.Button('Subir Archivo de Entrada', style={'font-size': '14px'}),
            style={'textAlign': 'center', 'margin-bottom': '20px'}
        )
    ]),

    # Mensaje de estado
    html.Div(id='status-message', style={'color': 'yellow', 'font-size': '14px', 'textAlign': 'center'}),

    # Gráfico y tabla basados en predictions_output.csv
    html.Div([
        html.H3('Cantidad de Registros Procesados en Predictions_output.csv', style={'color': '#9bb8b7'}),
        dcc.Graph(id='output-graph', style={'height': '400px'}),
        html.H3('Detalle de Predicciones', style={'color': '#9bb8b7'}),
        DataTable(
            id='predictions-table',
            style_table={'overflowX': 'auto', 'color': 'black', 'backgroundColor': 'white'},
            style_header={'backgroundColor': '#1f2630', 'color': 'white'},
            style_cell={'textAlign': 'left', 'font-size': '14px'}
        )
    ])
])

# Función de filtrado
def filter_dataframe(df, state, category, month):
    filtered_df = df.copy()
    if state != 'Todos' and state is not None:
        filtered_df = filtered_df[filtered_df['state'] == state]
    if category != 'Todas' and category is not None:
        filtered_df = filtered_df[filtered_df['category'] == category]
    if month != 'Todos' and month is not None:
        filtered_df = filtered_df[filtered_df['month'] == int(month)]
    return filtered_df

# Callback para actualizar gráficos
@app.callback(
    Output('heatmap', 'figure'),
    Output('gender-distribution', 'figure'),
    Output('category-distribution', 'figure'),
    Output('merchant-distribution', 'figure'),
    Output('weekly-hourly-frequency', 'figure'),
    [Input('state-filter', 'value'), Input('category-filter', 'value'), Input('month-filter', 'value'), Input('status-message', 'children')]
)
def update_graphs(state, category, month, mensaje_archivo = None):
    global df

    filtered_df = filter_dataframe(df, state, category, month)

    heatmap_fig = px.density_mapbox(
        filtered_df, lat='lat', lon='long', z='amt', radius=10,
        center=dict(lat=37.0902, lon=-95.7129), zoom=4,
        mapbox_style="carto-darkmatter"
    )

    gender_fig = px.pie(
        filtered_df, names='gender', title='Distribución de Género',
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    category_fig = px.bar(
        filtered_df['category'].value_counts().reset_index(),
        x='category', y='count', title='Distribución de Categorías de Transacción',
        labels={'category': 'Categoría', 'count': 'Cantidad'}
    )

    merchant_fig = px.bar(
        filtered_df['merchant'].value_counts().reset_index(),
        x='merchant', y='count', title='Transacciones Fraude por Mercado',
        labels={'merchant': 'Mercado', 'count': 'Cantidad'}
    )

    weekly_hourly_fig = px.density_heatmap(
        filtered_df, x='hour', y='day_of_week',
        title='Interacción por Franja Horaria y Día de la Semana',
        labels={'hour': 'Hora', 'day_of_week': 'Día de la Semana'},
        category_orders={'day_of_week': days_order}
    )

    for fig in [heatmap_fig, gender_fig, category_fig, merchant_fig, weekly_hourly_fig]:
        fig.update_layout(paper_bgcolor='#1f2630', font_color='white', plot_bgcolor='#1f2630')

    return heatmap_fig, gender_fig, category_fig, merchant_fig, weekly_hourly_fig

# Callback para procesar el archivo subido
@app.callback(
    [Output('status-message', 'children'), 
     Output('output-graph', 'figure'), 
     Output('predictions-table', 'data'),
     Output('predictions-table', 'columns')],
    [Input('upload-input', 'contents'), State('upload-input', 'filename'), Input('state-filter', 'value'), Input('category-filter', 'value'), Input('month-filter', 'value')],
)
def process_input_file(contents, filename, state, category, month):
    global df

    if contents is not None:
        # Decodificar y guardar el archivo subido
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        with open('predictions/archivo_input.csv', 'wb') as f:
            f.write(decoded)
        
        # Leer el archivo subido
        input_df = pd.read_csv('predictions/archivo_input.csv')
        
        # Generar predicciones
        input_df = realizar_prediccion(input_df)
        
        # Guardar el archivo procesado con las predicciones
        input_df.to_csv('predictions/predictions.csv', index=False)

        # Leer el archivo procesado y contar las predicciones
        output_df = pd.read_csv('predictions/predictions.csv', parse_dates=['trans_date_trans_time'])
        prediction_counts = output_df['Prediction'].value_counts()

        # Crear un gráfico de barras con las predicciones
        fig = px.bar(
            x=prediction_counts.index, 
            y=prediction_counts.values,
            labels={'x': 'Prediction', 'y': 'Cantidad'}, 
            text_auto=True,
            color=prediction_counts.index, 
            title='Distribución de Predicciones'
        )
        fig.update_layout(paper_bgcolor='#1f2630', font_color='white', plot_bgcolor='#1f2630')

        #Actualizo la data
        df = output_df.copy()
        df['date'] = df['trans_date_trans_time'].dt.date
        df['hour'] = df['trans_date_trans_time'].dt.hour
        df['day_of_week'] = df['trans_date_trans_time'].dt.day_name()
        df['month'] = df['trans_date_trans_time'].dt.month

        # Preparar datos para la tabla
        table_data = output_df.to_dict('records')  # Filas de datos
        table_columns = [{"name": col, "id": col} for col in output_df.columns]  # Nombres de columnas

        # Mensaje de éxito
        message = f'Archivo procesado con éxito: {filename}'
        return message, fig, table_data, table_columns

    # Si no hay archivo cargado, devuelve valores vacíos
    return 'Por favor, sube un archivo CSV para procesar.', px.bar(), [], []

if __name__ == '__main__':
    app.run_server(debug=True, port=8010)


# In[ ]:





# In[ ]:




