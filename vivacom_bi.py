import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, ClientsideFunction, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import glob
import pandas as pd
from dateutil.relativedelta import relativedelta
import datetime as dt
from babel.numbers import format_currency
from pesl import arquivos_pesl, calculo_pesl, tela_pesl

# =======================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
# ========================


########################### TRATAMENTO DE DADOS

dir = 'dataset'
dir_peona = '/BasePEONA_092023.txt'

names=['DATA', 'PLANO','RECEITAS','DESPESAS']
base_peona = pd.read_csv(dir+dir_peona,sep='#',names=names)
base_peona.DATA = pd.to_datetime(base_peona.DATA,format='%m/%Y')

celg_odonto = base_peona[base_peona.PLANO == 450109048].drop('PLANO',axis=1)
celg_saude = base_peona[base_peona.PLANO == 463295108].drop('PLANO',axis=1)
vivacom = base_peona.groupby([pd.Grouper(key = 'DATA', freq = 'M')]).sum().reset_index().drop('PLANO',axis=1)

anos = base_peona.DATA.drop_duplicates().sort_values(ascending=False).dt.strftime('%m-%Y').tolist()

def peona(data):  

    def calculo(base,data):
        data_inicio = pd.to_datetime(data) - relativedelta(months = 11)
        data_fim = pd.to_datetime(data) + relativedelta(months = 1)

        return round(max(base[(base.DATA >= data_inicio)&(base.DATA < data_fim)].RECEITAS.sum() * 0.085, base[(base.DATA >= data_inicio)&(base.DATA < data_fim)].DESPESAS.sum() * 0.1),2)

    peona_dict = {}
    peona_dict['VIVACOM'] = calculo(vivacom,data)
    peona_dict['CELG_SAUDE'] = calculo(celg_saude,data)
    peona_dict['CELG_ODONTO'] = round(peona_dict['VIVACOM'] - peona_dict['CELG_SAUDE'],2)
    
    return peona_dict


def tabela_peona(base,data):  

    data_inicio = pd.to_datetime(data) - relativedelta(months = 11)
    data_fim = pd.to_datetime(data) + relativedelta(months = 1)
    tabela = base[(base.DATA >= data_inicio)&(base.DATA < data_fim)].copy()
    tabela.DATA = tabela.DATA.astype(str).str[5:8] + tabela.DATA.astype(str).str[:4]
    return tabela


########################### GRÁFICOS

def rec_desp(base,data,titulo):

    x = tabela_peona(base,data).DATA 
    y1 =  tabela_peona(base,data).DESPESAS
    y2 =  tabela_peona(base,data).RECEITAS

    fig = go.Figure(data=[
        go.Bar(name='Receita', x=x, y = y2, textposition='auto',marker_color='#003e4c'), #text=[format_currency(v, 'BRL', locale='pt_BR') for v in y2],
        go.Bar(name='Despesa', x=x, y = y1, textposition='auto',marker_color='#a50000'), #text=[format_currency(v, 'BRL', locale='pt_BR') for v in y1],
    ])


    fig.update_traces(#marker_color='#a50000',    textposition='outside', 
        textfont_size=14,
        
        )

    # Change the bar mode
    fig.update_layout(
        margin=dict(l=50, r=10, t=50, ), #b=50
        barmode='group',height=360, width=820,
        legend_title_text = None,
        font_family="Neulis Alt",
        template='plotly_white',#None,
        #plot_bgcolor='white',
        

        title={
            'text': '<b>'+f'{titulo} - Receitas Assistenciais x Despesas Assistenciais'+'</b>',
            #'y':0.83,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        
        legend=dict(
        yanchor="bottom",
        y=-0.25,
        xanchor="right",
        x=0.65,
        orientation="h"),
        
        yaxis=dict(
            side="left",
            range=[0,max(max(tabela_peona(base,data).DESPESAS),max(tabela_peona(base,data).RECEITAS)) * 1.3],
            #autorange=True,
        ),
    )
    fig.update_yaxes(showspikes=True, mirror=True, showline=True)
    fig.update_xaxes(mirror=True, showline=True)
    return fig


########################### LAYOUT DASHBOARD

def card_peona(name):
    cardbody = dbc.Card([dbc.CardBody([
                                    html.H5(name, className="card-text")                                    
                                    ])
                                ], color="#a50000", outline=True,inverse=True, style={"margin-top": "20px","margin-left": "15px",
                                        "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                        #"color": "#FFFFFF"
                                        })
    return cardbody


def card(name,id):
    cardbody = dbc.Card([dbc.CardBody([
                                    html.H5(name, className="card-text"),
                                    html.H4(#style={"color": "#5d8aa7"}, 
                                            id=id),
                                    ])
                                ], color="#003e4c", outline=True,inverse=True, style={"margin-top": "20px","margin-left": "15px",
                                        "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                                        #"color": "#FFFFFF"
                                        })
    return cardbody

def header():
    header_geral = html.Div([
        html.Div([
            dbc.Row([
                dbc.Col(
                    html.H3(
                        dbc.Badge(
                            "VIVACOM",
                            color="#a50000",
                            className="me-1",
                                    )
                        )
                    ),
                    dbc.Col([
                        html.Img(
                            id="logo",
                            src=app.get_asset_url("logo.png"),
                            height=50,
                            )
                        ],style={"textAlign": "right"},),
                    ]),
                ],style={
                    "background-color": "#003e4c",  # 003e4c",
                    "margin": "0px",
                    "padding": "20px",
                    },
        ),
        html.Div([
            dbc.Nav([
                dbc.Navbar(
                    dbc.Container(
                        children=[
                            dbc.NavItem(
                                dbc.NavLink(
                                    "PEONA   ",
                                    href="/peona",
                                    className="nav-link",
                                    ),
                                    style={
                                        "margin": "-20px",
                                        "margin-left": "20px",
                                    },
                                ),
                            dbc.NavItem(
                                dbc.NavLink('Margem de Solvência   ',
                                             href='/prestadores', 
                                             className="nav-link"),
                                             style={"margin": "-20px",
                                                    "margin-left": "20px"},),
                            dbc.NavItem(
                                dbc.NavLink('PESL   ',
                                             href='/pesl', 
                                             className="nav-link"),
                                             style={"margin": "-20px",
                                                    "margin-left": "20px"},),
                                    ],
                            fluid=True,
                        ),
                        color="light",
                        dark=False,
                        # class_name='collapse navbar-collapse',
                    )
                ],class_name="navbar navbar-light bg-light",),
                # ]),
            ]),
    ])

    return header_geral

tela_peona = html.Div(children=[
        dbc.Row([
            header()
                ]),

            dbc.Row([
                dbc.Col([
                    html.H5(
                        dbc.Badge(
                            "Filtrar pela competência:",
                            color="#5d8aa7",
                            className="me-1",
                            style={
                                "margin-left": "25px",
                                "margin-top": "10px",
                                },
                                    )
                            ),
                        dcc.Dropdown(
                            id="select-ano",
                            value=anos[0],
                            options=[
                                {
                                    "label": i,
                                    "value": i,
                                }
                                for i in anos
                            ],
                            placeholder="Selecione o período",
                            style={
                                #"width": "60%",
                                #'padding': '3px',
                                "margin-left": "10px",
                                #'font-size':'18px',
                                "textAlign": "center",
                            },
                            ),
                card_peona("PEONA"),
                card("CELGODONTO","peona_celgodonto"),
                card("CELGSAÚDE","peona_celgsaude"),
                card("VIVACOM","peona_vivacom"),
                        ], width=2),

                dbc.Col([
                        html.Div([], id='tabela_peona'),                
                        ], width=3,
                        style={"margin-left": "15px",
                                 "margin-top": "15px",},
                         ),

                dbc.Col([
                        dcc.Graph(id="graph_celgsaude",
                          style={"margin-top": "0px",
                                 "margin-left": "-15px",},),

                        dcc.Graph(id="graph_celgodonto",
                          style={"margin-top": "-15px",
                                 "margin-left": "-15px",},),
                        ])#, width=1),

                ]),


    ])


app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

@app.callback(
    [   Output("peona_vivacom", 'children'),
        Output("peona_celgsaude", 'children'),
        Output("peona_celgodonto", 'children'),        
    ],
Input('select-ano', 'value'),
)

def update_cards(data):
    data = pd.to_datetime(data)
    return [format_currency(peona(data)[x], 'BRL', locale='pt_BR') for x in peona(data)]


@app.callback(
    Output('tabela_peona','children'),    
    Input('select-ano', 'value'),
)
def update_table(data):

    data = pd.to_datetime(data)
    tabela_peona_dash = tabela_peona(vivacom,data)
    tabela_peona_dash = pd.concat([tabela_peona_dash,pd.DataFrame({
                "DATA": ["TOTAL"],
                "DESPESAS": [tabela_peona_dash["DESPESAS"].sum()],
                "RECEITAS": [tabela_peona_dash["RECEITAS"].sum()],
            }
        ),
    ]
)
    tabela_peona_dash.DESPESAS = [format_currency(v, 'BRL', locale='pt_BR') for v in tabela_peona_dash.DESPESAS]
    tabela_peona_dash.RECEITAS = [format_currency(v, 'BRL', locale='pt_BR') for v in tabela_peona_dash.RECEITAS]


    tabela = dash_table.DataTable(
        columns=[
            {"name": i,
             "id": i,
             "deletable": False, }
            for i in tabela_peona_dash.columns
            if i != "id"
        ],
        data=tabela_peona_dash.to_dict("records"),
        style_as_list_view=True,
        style_header={
            "backgroundColor": "#003e4c",
            "color": "white",
            "fontWeight": "bold",
            "text-align": "center",
            "fontSize": 14,
        },
        style_data_conditional=[
            {"if": {"column_id": "DATA"},
             "textAlign": "left", },
        ],
        style_cell={
            "padding": "8px",
            "font-family": "Helvetica",
            "fontSize": 13,
            "color": "#5d8aa7",
            "fontWeight": "bold",
        },
        fill_width=True,
        fixed_rows={'headers': True},
        #filter_action="native",
        #page_size=10,
        #filter_options={
        #    "case": "insensitive",
        #    "placeholder_text": "Filtrar Tabela (digite e tecle Enter)",
        #},
        style_data={
            "userSelect": "none"
        },
        style_table={#'height': '450px',
                     'overflowY': 'auto',
                     },
    )

    return tabela

@app.callback(
    [   Output("graph_celgsaude", 'figure'),
        Output("graph_celgodonto", 'figure'),        
    ],
Input('select-ano', 'value'),
)

def update_graphs(data):
    data = pd.to_datetime(data)
    return [rec_desp(celg_saude,data,'CELGSAÚDE'),rec_desp(celg_odonto,data,'CELGODONTO')]

# PESL ===============================    

@app.callback(
    Output('tabela_pesl','children'),    
    Input('select-ano2', 'value'),
)
def update_table_pesl(data):

    tabela_pesl = calculo_pesl(data)
    for i in tabela_pesl.columns[1:]:
            tabela_pesl[i] = [format_currency(v + 0.0, "BRL", locale="pt_BR") for v in tabela_pesl[i]]

    tabela = dash_table.DataTable(
        columns=[
            {"name": i,
             "id": i,
             "deletable": False, }
            for i in tabela_pesl.columns
            if i != "id"
        ],
        data=tabela_pesl.to_dict("records"),
        style_as_list_view=True,
        style_header={
            "backgroundColor": "#003e4c",
            "color": "white",
            "fontWeight": "bold",
            "text-align": "center",
            "fontSize": 14,
        },
        style_data_conditional=[
            {"if": {"column_id": "DATA"},
             "textAlign": "left", },
        ],
        style_cell={
            "padding": "8px",
            "font-family": "Helvetica",
            "fontSize": 13,
            "color": "#5d8aa7",
            "fontWeight": "bold",
        },
        fill_width=True,
        #fixed_rows={'headers': True},
        style_data={
            "userSelect": "none"
        },
        style_table={#'height': '450px',
                     #'overflowY': 'auto',
                     },
    )

    return tabela

@app.callback(
        Output("graph_pesl", 'figure'),
        Input('select-ano2', 'value'),
)
def update_gprah_pesl(data):

    tabela_pesl = calculo_pesl(data)
    pie = tabela_pesl[['Não Vinculado','Vinculado']].T

    text_format = [format_currency(v, "BRL", locale="pt_BR")for v in pie['Total']]
    fig = px.pie(pie, values='Total',names=pie.index,
                color_discrete_sequence=['#003e4c',
                                         '#a50000']#px.colors.sequential.RdBu[-1],px.colors.sequential.RdBu[1]],
                )

    fig.update_layout(
        
        separators=',.',
        barmode='group',
        height=540, width=720,
        legend_title_text = None,
        font_family="Neulis Alt",
        
        title={
            'text': '<b>'+'PESL - Vinculado x Não Vinculado'+'</b>',
#            'y':1,
            'x':0.45,
            'xanchor': 'center',
            'yanchor': 'top'},

        legend=dict(
        yanchor="auto",
        #y=0.5,
        xanchor="left",
        #x=1,
        orientation="v")
    )

    fig.update_traces(
        rotation= 90,
        text=text_format,
        textinfo='label+text+percent',
        hovertemplate='%{label}: R$ %{value:,.2f} <br>%{percent}',
        #textposition='outside'
        )

    return fig



# Update page =========================

@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")],
)
def display_page(pathname):
    if (
        pathname == "/peona"
        or pathname == "/"
    ):
        return tela_peona
    elif pathname == '/prestadores':
        return tela_peona
    
    elif pathname == '/pesl':
        return tela_pesl()
        
    else:
        return tela_peona

#======================================

if __name__ == "__main__":
    app.run_server(debug=False)  # , port=8051)
