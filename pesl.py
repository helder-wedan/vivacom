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
import requests
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])


dir = 'dataset'
dir_peona = '/BasePEONA_092023.txt'
names=['DATA', 'PLANO','RECEITAS','DESPESAS']

base_peona = pd.read_csv(dir+dir_peona,sep='#',names=names)
base_peona.DATA = pd.to_datetime(base_peona.DATA,format='%m/%Y')
anos = base_peona.DATA.drop_duplicates().sort_values(ascending=False).dt.strftime('%m-%Y').tolist()

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

arquivos_pesl = pd.read_csv('dataset/pesl_2023_09.csv')

def calculo_pesl(data):
    mes = pd.to_datetime(data)
    mes_inicio = mes - relativedelta(months=1)
    mes_fim = mes + relativedelta(months=1)
    base_pesl = arquivos_pesl[arquivos_pesl.competencia == data].copy()
    base_pesl.DATA = pd.to_datetime(base_pesl.DATA,format='%Y-%m-%d')
    pesl = base_pesl[(base_pesl.DATA >= mes_inicio.strftime('%m-%Y'))&(base_pesl.DATA < mes_fim)]#.sum(numeric_only=True)
    pesl = pesl.groupby(pesl.DATA.dt.year).sum(numeric_only=True).reset_index()
    vinculado = base_pesl.groupby(base_pesl.DATA.dt.year).sum(numeric_only=True).reset_index()
    tabela = pesl.merge(vinculado,on='DATA',how='right').fillna(0.00)
    tabela.DATA = tabela.DATA.astype(int)
    tabela.columns=['Data','Não Vinculado','PESL']
    tabela['Vinculado']= tabela['PESL'] - tabela['Não Vinculado']
    tabela.loc['Total'] = tabela[tabela.columns[1:]].sum(numeric_only=True) #tabela.sum(numeric_only=True)
    return tabela[['Data','Não Vinculado','Vinculado','PESL']].fillna('Total')
    
def tela_pesl():
    tela_pesl = html.Div(children=[
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
                            id="select-ano2",
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
                            dcc.Loading(
                                id="loading-1",
                                type="dot",
                                style={
                                    "margin-top": "40px",
                                },
                            ),
                    
                        ], width=2),

                dbc.Col([
                        html.Div([], id='tabela_pesl'),                
                        ], width=4,
                        style={"margin-left": "15px",
                                 "margin-top": "15px",},
                         ),

                dbc.Col([
                        dcc.Graph(id="graph_pesl",
                          style={"margin-top": "0px",
                                 "margin-left": "-15px",},),
                        ])#, width=1),

                ]),

    ])
    return tela_pesl
