# server modules
from cliente import Cliente
import threading
import numpy as np

# gui modules
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State
import plotly.graph_objs as go
import plotly

# file saving modules
import json
import pandas as pd
from collections import deque

# other modules
import datetime
import os

# controller module
from PID import PID


# global control system attributes
class System:
    def __init__(self, maxlen=100):
        # historic times list
        self.ts = deque(maxlen=maxlen)
        # historic heights list
        self.h1 = deque(maxlen=maxlen)
        self.h2 = deque(maxlen=maxlen)
        self.h3 = deque(maxlen=maxlen)
        self.h4 = deque(maxlen=maxlen)
        # historic valves list
        self.v1 = deque(maxlen=maxlen)
        self.v2 = deque(maxlen=maxlen)
        # system pids initialization
        self.pid1 = PID()
        self.pid2 = PID()
        # saving memory
        self.memory = []
        self.ti = 0
        # seconds for sinusoid plotting
        self.sec = 0
        # events
        self.event_color = 0
        self.event_text = 0
        self.event_save = 0

# threads management
class SubHandler(object):
    def datachange_notification(self, node, val, data):
        thread_handler = threading.Thread(target=function_handler, args=(node, val))
        thread_handler.start()

    def event_notification(self, event):
        system.event_color = event
        system.event_text = event

def function_handler(node, val):
    key = node.get_parent().get_display_name().Text
    print('key: {} | val: {}'.format(key, val))

# checks app history directory existence
directory = 'AppHistory'
if not os.path.exists(directory):
    os.makedirs(directory)

# initialize system variables
system = System()

# initialize client
cliente = Cliente("opc.tcp://localhost:4840/freeopcua/server/", suscribir_eventos=True, SubHandler=SubHandler)
cliente.conectar()

# Dash settings
colors = {'background': '#022B3A','text': '#f1faee'}
fonts = {'text': 'Helvetica'}
frequency = 1

# Dash layout
app = dash.Dash()
app.layout = html.Div(style={'backgroundColor': colors['background'], 'font-family': fonts['text']}, children=[
                html.H1(children='Aplicación de Control', style={'textAlign': 'center','color': '#022B3A', 'paddingTop': '20px', 'paddingBottom': '10px', 'backgroundColor': '#FFFFFF'}),
                dcc.Interval(id='interval-component', interval=int(1/frequency*1000), n_intervals=0),
                html.H2('Tanques', style={'textAlign': 'center', 'color': colors['text']}),
                html.Div(id='live-update-text1', style={'textAlign': 'center', 'padding':'15px', 'color': colors['text']}),
                dcc.Graph(id='live-update-graph1'), html.Div(id='intermediate', style={'display':'none'}),
                html.Div(id='GuardarDiv', style={'paddingBottom':'30px', 'textAlign': 'center', 'color': colors['text']}, children=[
                html.Button('Guardar Datos', id='guardar', n_clicks=0),
                html.Button('Dejar de Guardar', id='noguardar', n_clicks=0),
                html.Div(id='indicativoGuardar', children=['No guardando']),
                dcc.RadioItems(id='Formato', options=[{'label': '.csv', 'value': 'csv'}, {'label':'.json', 'value': 'json'}, {'label':'.pickle', 'value': 'pickle'}], value='csv')]),
                html.H2('Válvulas', style={'textAlign': 'center', 'color': colors['text']}),
                html.Div(dcc.Graph(id='live-update-graph2')),
                html.Div(id='Modo',style={'textAlign': 'center', 'color': colors['text']}, children=[
                    html.H2('Controlador'),
                    dcc.RadioItems(id='Eleccion',options=[{'label': 'Manual', 'value': 'Manual'}, {'label': 'Automático', 'value': 'Automatico'}], value='Manual'),
                    html.Div(id='MyDiv')]),
                html.Div(id='Modos',className='row' ,children=[
                    html.Div(id='Manual', className='six columns', style={'color': colors['text'], 'borderStyle': 'solid', 'borderWidth': '5px', 'borderColor': '#1F7A8C'}, children=[
                        html.H3('Modo Manual', style={'textAlign': 'center'}),
                        html.H4('Valor de las Razones'),
                        html.Div(id='RazonesDiv', className='row', children=[
                            html.Div(id='Razon1Div', style={'paddingBottom':'50px'},className='six columns', children=[
                                html.Label(id='Razon1Label', children='Razon 1'),
                                dcc.Slider(id='Razon1', min=0, max=1, step=0.05, value=0.7)]),
                            html.Div(id='Razon2Div', style={'paddingBottom':'50px'}, className='six columns', children=[
                                html.Label(id='Razon2Label',children='Razon 2'),
                                dcc.Slider(id='Razon2', min=0, max=1, step=0.05, value=0.6)])
                        ]),
                        dcc.RadioItems(id='TipoManual', options=[{'label': 'Sinusoide', 'value': 'sinusoide'}, {'label':'Valor Fijo', 'value':'fijo'}], value='fijo'),
                        html.H4('Sinusoide'),
                        html.Div(id='Sliders1', className='row', children=[
                            html.Div(id='Frec', style={'paddingBottom':'50px'}, className='six columns', children=[
                                html.Label(id='1',children='Frec'), dcc.Slider(id='FrecSlider',min=frequency/25, max=frequency/2, step=0.1, value=frequency/4, vertical=False)]),
                            html.Div(id='Amp', className='six columns', children=[
                                html.Label(id='2', children='Amp'), dcc.Slider(id='AmpSlider',min=0.1, max=1, step=0.05, value=1, vertical=False)])]),
                        html.Div(id='Sliders2', className='row', children=[
                            html.Div(id='Fase', style={'paddingBottom':'50px'}, className='six columns', children=[
                                html.Label(id='3', children='Fase'), dcc.Slider(id='FaseSlider',min=0, max=6.28, step=0.1, value=0, vertical=False)]),
                            html.Div(id='Offset', className='six columns', children=[
                                html.Label(id='4', children='Offset'), dcc.Slider(id='OffsetSlider',min=1, max=3, step=0.05, value=0, vertical=False)])]),
                        html.H4('Valor fijo'),
                        html.Div(style={'textAlign':'center', 'paddingBottom':'10px'},children=[dcc.Input(id='ManualFijo',placeholder='Ingrese un valor entre -1 y 1 ...', type='text', value='0')])
                    ]),
                    html.Div(id='Automatico', className='six columns', style={'color': colors['text'], 'borderStyle': 'solid', 'borderWidth': '5px', 'borderColor': '#1F7A8C'}, children=[
                        html.H3('Modo Automatico', style={'textAlign': 'center'}),
                        html.H4('SetPoints'),
                        html.Div(id='SetPoints', className='row', children=[
                            html.Div(id='Tanque1', className='six columns', children=[
                                html.Label('SetPoint Tanque 1'), dcc.Input(id='SPT1', placeholder='Ingrese valor', type='text', value='25')]),
                            html.Div(id='Tanque2', className='six columns', children=[
                                html.Label('SetPoint Tanque 2'), dcc.Input(id='SPT2', placeholder='Ingrese valor', type='text', value='25')])
                        ]),
                        html.H4('Constantes del PID'),
                        html.Div(id='constantes1', className='row', children=[
                            html.Div(id='P', className='six columns', children=[
                                html.Label('Proporcional'),
                                dcc.Input(id='kp',placeholder='Ingrese un valor', type='text', value='0.1')]),
                            html.Div(id='I', className='six columns', children=[
                                html.Label('Integral'),
                                dcc.Input(id='ki',placeholder='Ingrese un valor', type='text', value='0.1')])]),
                        html.Div(id='constantes2', className='row',  style={'paddingBottom':'10px'},children=[
                            html.Div(id='D', className='six columns', children=[
                                html.Label('Derivativa'),
                                dcc.Input(id='kd',placeholder='Ingrese un valor', type='text', value='0')]),
                            html.Div(id='W', className='six columns', children=[
                                html.Label('Anti wind-up'),
                                dcc.Input(id='kw',placeholder='Ingrese un valor', type='text', value='0')])])
                    ])
                ]),
                html.Div(id='AlarmaContainer', style={'paddingTop': '20px', 'paddingBottom': '10px'}, children=[
                    html.Div(id='Alarma', style={'backgroundColor': '#006400', 'width': '80%', 'height': '70px', 'paddingTop':'25px', 'margin':'auto','borderStyle': 'solid', 'borderWidth': '5px', 'borderColor': '#1F7A8C'}, children=[
                        html.H2(id='AlarmaTexto',style={'textAlign':'center', 'color': colors['text'], 'paddingBottom':'40px'}, children=['Alarma Inactiva'])
                    ])
                ])

]
)

# alarm color callback function
@app.callback(Output('Alarma', 'style'), [Input('interval-component', 'n_intervals')])
def alarm_color(n):
    if system.event_color != 0:
        color = '#EF2D56'
    else:
        color = '#8CD867'
    system.event_color = 0

    style = {'backgroundColor': color, 'font-family': fonts['text'], 'color': colors['text'],  'width': '80%', 'height': '70px', 'paddingTop': '25px', 'margin': 'auto',
                'borderStyle': 'solid', 'borderWidth': '5px', 'borderColor': '#1F7A8C'}
    return style

# alarm text callback function
@app.callback(Output('AlarmaTexto', 'children'), [Input('interval-component', 'n_intervals')])
def alarm_text(n):
    if system.event_text != 0:
        mensaje = system.event_text.Message.Text.split(':')
        res = 'Alarma Activa: {}: {}'.format(mensaje[1], round(float(mensaje[2]), 2))
    else:
        res = 'Alarma Inactiva'
    system.event_text = 0
    return res

# save callback function
@app.callback(Output('indicativoGuardar', 'children'), [Input('guardar', 'n_clicks'), Input('noguardar', 'n_clicks')])
def save(n_clicks, no_guardar):
    if system.event_save != n_clicks:
        system.event_save = n_clicks
        return 'Guardando'
    else:
        return 'No Guardando'

# heights update callback function
@app.callback(Output('intermediate', 'children'), [Input('interval-component', 'n_intervals')])
def update_heights(n):
    heights = {f'h{i}': cliente.alturas[f'H{i}'].get_value() for i in range(1, 5)}
    return json.dumps(heights)

# heights text update callback function
@app.callback(Output('live-update-text1', 'children'), [Input('intermediate', 'children')])
def update_text(heights):
    heights = json.loads(heights)
    style = {'padding': '10px', 'fontSize': '16px'}#, 'border': '2px solid', 'borderColor': '#1F7A8C'}
    return [
        html.Span('Tanque 1: {}'.format(round(heights['h1'], 2)), style=style),
        html.Span('Tanque 2: {}'.format(round(heights['h2'], 2)), style=style),
        html.Span('Tanque 3: {}'.format(round(heights['h3'], 2)), style=style),
        html.Span('Tanque 4: {}'.format(round(heights['h4'], 2)), style=style)
    ]

# heights graph update callback function
@app.callback(Output('live-update-graph1', 'figure'), [Input('intermediate', 'children')])
def update_graph(heights):
    heights = json.loads(heights)
    # save last height to height history
    system.h1.append(heights['h1'])
    system.h2.append(heights['h2'])
    system.h3.append(heights['h3'])
    system.h4.append(heights['h4'])

    # make plot for every tank height
    plot1 = go.Scatter(x=list(system.ts), y=list(system.h1), name='Tanque1', mode='lines+markers')
    plot2 = go.Scatter(x=list(system.ts), y=list(system.h2), name='Tanque2', mode='lines+markers')
    plot3 = go.Scatter(x=list(system.ts), y=list(system.h3), name='Tanque3', mode='lines+markers')
    plot4 = go.Scatter(x=list(system.ts), y=list(system.h4), name='Tanque4', mode='lines+markers')

    # create figure to fit the four plots
    fig = plotly.tools.make_subplots(rows=2, cols=2, vertical_spacing=0.2,
                                     subplot_titles=('Tanque1', 'Tanque2', 'Tanque3', 'Tanque4'), print_grid=False)
    fig['layout']['margin'] = {
        'l': 30, 'r': 10, 'b': 30, 't': 30
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    fig['layout']['plot_bgcolor'] = colors['background']
    fig['layout']['paper_bgcolor'] = colors['background']
    fig['layout']['font']['color'] = colors['text']
    
    # set plot positions in figure
    fig.append_trace(plot1, 1, 1)
    fig.append_trace(plot2, 1, 2)
    fig.append_trace(plot3, 2, 1)
    fig.append_trace(plot4, 2, 2)

    return fig

################################################# Control ##############################################################
# chosen method text callback function
@app.callback(Output(component_id='MyDiv', component_property='children'),
    [Input(component_id='Eleccion', component_property='value')])
def update_output_div(input_value):
    return f'Ha seleccionado el modo: {input_value}'

#################### Modo Manual ##################################
# frequency value callback function
@app.callback(Output('1', 'children'), [Input('FrecSlider', 'value')])
def update_label_1(value):
    return f'Frec: {value} Hz'
# amplitude value callback function
@app.callback(Output('2', 'children'), [Input('AmpSlider', 'value')])
def update_label_2(value):
    return f'Amp: {value}'
# phase value callback function
@app.callback(Output('3', 'children'), [Input('FaseSlider', 'value')])
def update_label_3(value):
    return f'Fase: {value}'
# offset value callback function
@app.callback(Output('4', 'children'), [Input('OffsetSlider', 'value')])
def update_label_4(value):
    return f'Offset: {value}'
# rate 1 value callback function
@app.callback(Output('Razon1Label', 'children'), [Input('Razon1', 'value')])
def update_rate_1(value):
    return f'Razon 1: {value}'
# rate 2 value callback function
@app.callback(Output('Razon2Label', 'children'), [Input('Razon2', 'value')])
def update_rate_2(value):
    return f'Razon 2: {value}'


#################### Modo Automático ##############################
# pid controller updating and output plotting
@app.callback(Output('live-update-graph2', 'figure'),
              [Input('intermediate', 'children')],
              [State('Eleccion', 'value'), State('TipoManual', 'value'),
                State('FrecSlider', 'value'),State('AmpSlider', 'value'),
                State('OffsetSlider', 'value'),State('FaseSlider', 'value'),
                State('ManualFijo', 'value'), State('kp', 'value'),
                State('ki', 'value'), State('kd', 'value'), State('kw','value'),
                State('SPT1', 'value'), State('SPT2', 'value'),
                State('indicativoGuardar', 'children'), State('Formato', 'value'),
                State('Razon1', 'value'), State('Razon2', 'value')])
def controller_output(heights, choice, manual_type, freq, amp, offset, phase, fixed,
                      kp, ki, kd, kw, SPT1, SPT2, saving, formatting, rate_1, rate_2):
    heights = json.loads(heights)
    # set current time and save to historical times
    now = datetime.datetime.now()
    system.ts.append(now)
    v1 = v2 = 0
    # set valves rates
    cliente.razones['razon1'].set_value(rate_1)
    cliente.razones['razon2'].set_value(rate_2)

    if choice == 'Manual' and manual_type == 'sinusoide':
        # put a sinusoid on the valve rates 
        v1 = v2 = amp * np.cos(2 * np.pi * freq * system.sec + phase) + offset
        system.sec += 1 / frequency

    elif choice == 'Manual' and manual_type == 'fijo':
        # fix valve rates
        v1 = v2 = float(fixed)

    elif choice == 'Automatico':
        # pass set points to pid controller
        system.pid1.ref = float(SPT1)
        system.pid2.ref = float(SPT2)

        # pass constants to pid controller
        system.pid1.kp = system.pid2.kp = float(kp)
        system.pid1.ki = system.pid2.ki = float(ki)
        system.pid1.kd = system.pid2.kd = float(kd)
        system.pid1.kw = system.pid2.kw = float(kw)

        # update valve rates based on pid controller output
        v1 = system.pid1.update(heights['h1'])
        v2 = system.pid2.update(heights['h2'])

    if saving == 'Guardando':
        if system.memory == []:
            system.ti = datetime.datetime.now()

        if choice == 'Manual':
            system.memory.append({'time':now,'h1': heights['h1'], 'h2': heights['h2'], 'h3': heights['h3'], 'h4': heights['h4'],
                            'v1': v1, 'v2':v2, 'modo': '{}-{}'.format(choice, manual_type)})
        else:
            system.memory.append(
                {'time': now, 'h1': heights['h1'], 'h2': heights['h2'], 'h3': heights['h3'], 'h4': heights['h4'],
                 'v1': v1, 'v2': v2, 'modo': '{}'.format(choice), 'sp1': float(SPT1), 'sp2': float(SPT2),
                 'ki': float(ki),'kd': float(kd),'kp': float(kp),'kw': float(kw)})

    elif saving == 'No guardando' and system.memory != []:
        system.memory = pd.DataFrame(system.memory)
        system.memory = system.memory.set_index('time')
        if formatting == 'csv':
            system.memory.to_csv(f'{directory}/{system.ti}-{now}.csv')
        elif formatting == 'json':
            system.memory.to_json(f'{directory}/{system.ti}-{now}.json')
        else:
            system.memory.to_pickle(f'{directory}/{system.ti}-{now}.pkl')
        system.memory = []


    cliente.valvulas['valvula1'].set_value(v1)
    cliente.valvulas['valvula2'].set_value(v2)

    system.v1.append(v1)
    system.v2.append(v2)

    plot1 = go.Scatter(x=list(system.ts), y=list(system.v1), name='Valvula1', mode='lines+markers')
    plot2 = go.Scatter(x=list(system.ts), y=list(system.v2), name='Valvula2', mode='lines+markers')


    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2,
                                     subplot_titles=('Valvula1', 'Valvula2'), print_grid=False)
    fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 30, 't': 30}
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    fig['layout']['plot_bgcolor'] = colors['background']
    fig['layout']['paper_bgcolor'] = colors['background']
    fig['layout']['font']['color'] = colors['text']

    # fig['layout'].update(height=600, width=600, title='Niveles de los Tanques')
    fig.append_trace(plot1, 1, 1)
    fig.append_trace(plot2, 2, 1)

    return fig

app.run_server(debug=False)
