import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, callback
from pymongo import MongoClient
import pandas as pd
import numpy as np
import dash



user = "gwCode"
pwd = "greenwayServerlessTest"
client = MongoClient(
    f"mongodb://{user}:{pwd}@10.0.140.199:17273/?authMechanism=DEFAULT&authSource=greenwayFullfilmentTest"
)
db = "greenwayFullfilmentTest"
collection = "targets"


pipeline = [
    {"$match": {"isDeleted": False}},
    {"$sort": {"createdAt": -1}},
    {
        "$group": {
            "_id": "$targetYear",
            "totalTarget": {"$sum": "$targetCount"},
            "yearTarget": {"$sum": "$targetCount"},
            "monthDetail": {
                "$push": {
                    "Month": {
                        "$function": {
                            "body": 'function(month){\n            let defaultMonthList = [\n                  {\n                    text: "April",\n                    value: "4"\n                  },\n                  {\n                      text: "May",\n                      value: "5"\n                  },\n                  {\n                      text: "June",\n                      value: "6"\n                  }, {\n                      text: "July",\n                      value: "7"\n                  }, {\n                      text: "August",\n                      value: "8"\n                  }, {\n                      text: "September",\n                      value: "9"\n                  }, {\n                      text: "October",\n                      value: "10"\n                  }, {\n                      text: "November",\n                      value: "11"\n                  },\n                  {\n                      text: "December",\n                      value: "12"\n                  },\n                  {\n                      text: "January",\n                      value: "1"\n                  },\n                  {\n                      text: "February",\n                      value: "2"\n                  },\n                  {\n                      text: "March",\n                      value: "3"\n                  }\n              ];\n              return defaultMonthList.filter((item) => { if (month == item.value) { return item } })[0].text;\n          }',
                            "args": ["$targetMonth"],
                            "lang": "js",
                        }
                    },
                    "Asm": {"$ifNull": ["$asmName", ""]},
                    "SalesOfficer": {"$ifNull": ["$soName", ""]},
                    "Aso": {"$ifNull": ["$asoName", ""]},
                    "FieldOfficerName": "$foName",
                    "MonthTarget": "$targetCount",
                    "ACHIVEMENT": "$achievedCount",
                }
            },
        }
    },
    {"$unwind": {"path": "$monthDetail", "preserveNullAndEmptyArrays": False}},
    {
        "$replaceRoot": {
            "newRoot": {
                "$mergeObjects": [
                    {
                        "TargetYear": "$_id",
                        "TotalTarget": "$totalTarget",
                        "YearTarget": "$yearTarget",
                    },
                    "$monthDetail",
                ]
            }
        }
    },
]


df = pd.DataFrame(list(client[db][collection].aggregate(pipeline)))

colorScheme = px.colors.sequential.Bluyl_r
fontStyle = dict(family="Arial", color="black")


def createGraphs(dataFrame):
    colorScheme = px.colors.sequential.Bluyl_r
    fontStyle = dict(family="Times New Roman")

    AsmPie = px.pie(
        data_frame=dataFrame,
        values=dataFrame["MonthTarget"],
        names=dataFrame["Asm"],
        title="Assistant Sales Manager",
        labels={"MonthTarget": "Monthly Target"},
    )
    AsmPie.update_traces(
        textposition="inside",
        automargin=True,
        marker={"line": {"width": 2, "color": "white"}},
        textinfo="value+label",
    )
    AsmPie.update_layout(
        font=dict(family="Arial", size=15, color="black"),
        title="Assistant Sales Manager",
        title_x=0.5,
        legend=dict(title_text=" ", traceorder="normal", x=0.85),
    )
    
    SalesOfficerBar = go.Figure()
    SalesOfficerBar.add_trace(go.Histogram(histfunc="sum", y=dataFrame["MonthTarget"], x=dataFrame["SalesOfficer"], name="Monthly Sum", 
                                       textfont_size=15, texttemplate="%{y}"  ))
    SalesOfficerBar.add_trace(go.Histogram(histfunc="sum", y=dataFrame["ACHIVEMENT"], x=dataFrame["SalesOfficer"], name="Achivement sum",
                                      textfont_size=15, texttemplate="%{y}"))

    SalesOfficerBar.update_traces(
        textposition="inside",  marker={"line": {"width": 0, "color": "white"}}
    )
    SalesOfficerBar.update_layout(bargap=0.2,
        font=dict(family="Arial", size=15, color="black"),
        title="Sales Officer",
        title_x=0.5,
        plot_bgcolor="white",
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="  ",
        yaxis_title="  ",
    )

    AsoBar = go.Figure()
    AsoBar.add_trace(go.Histogram(histfunc="sum", y=dataFrame["MonthTarget"], x=dataFrame["Aso"], name="Monthly Sum", 
                                       textfont_size=15, texttemplate="%{y}"  ))
    AsoBar.add_trace(go.Histogram(histfunc="sum", y=dataFrame["ACHIVEMENT"], x=dataFrame["Aso"], name="Achivement sum",
                                      textfont_size=15, texttemplate="%{y}"))

    AsoBar.update_traces(
        textposition="inside",  marker={"line": {"width": 0, "color": "white"}}
    )
    AsoBar.update_layout(bargap=0.2,
        font=dict(family="Arial", size=15, color="black"),
        title="Sales Officer",
        title_x=0.5,
        plot_bgcolor="white",
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="  ",
        yaxis_title="  ",
    )
    
    FieldOfficerNameBar = go.Figure()
    FieldOfficerNameBar.add_trace(go.Histogram(histfunc="sum", y=dataFrame["MonthTarget"], x=dataFrame["FieldOfficerName"],name="Monthly Sum", 
                                       textfont_size=15, texttemplate="%{y}"))
    FieldOfficerNameBar.add_trace(go.Histogram(histfunc="sum", y=dataFrame["ACHIVEMENT"], x=dataFrame["FieldOfficerName"],name="Achivement sum",
                                      textfont_size=15, texttemplate="%{y}"))

    FieldOfficerNameBar.update_traces(
        textposition="inside",  marker={"line": {"width": 0, "color": "white"}}
    )
    FieldOfficerNameBar.update_layout( bargap=0.1,
        font=dict(family="Arial", size=15, color="black"),
        title="Sales Officer",
        title_x=0.5,
        plot_bgcolor="white",
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="  ",
        yaxis_title="  ",
    )

    return (
        f"Sum of Monthly Taret: {dataFrame['MonthTarget'].sum()}",
        f"Sum of Achivement: {dataFrame['ACHIVEMENT'].sum()}",
        AsmPie,
        SalesOfficerBar,
        AsoBar,
        FieldOfficerNameBar,
    )


app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.H1(
            "Statistics Dashboard",
            style={"fontSize": 30, "textAlign": "center"},
        ),
        html.Div(
            dcc.Dropdown(
                id="MonthFilter",
                placeholder="Select Month",
                style={"width": "100%"},
                options=sorted(df["Month"].unique()),
                # value= True,
                multi=True,
            ),
        ),
        html.Hr(),
        html.Div(
            [
                html.Button(
                    'Reset', id='resetPies', style={'width': '30%'}
                           ),
                html.Div(
                    id="MonthlySum", style={"width": "100%", "textAlign": "center"}
                ),
                html.Div(
                    id="AchivementSum", style={"width": "100%", "textAlign": "center"}
                ),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Hr(),
        html.Div(
            [
                dcc.Graph(id="Asm", style={"width": "50%"}),
                dcc.Graph(id="SalesOfficerr", style={"width": "50%"}),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="Asoo", style={"width": "50%"}),
                dcc.Graph(id="FieldOfficerNamee", style={"width": "50%"}),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        
    ]
)


@callback(
    [
        Output(component_id="MonthlySum", component_property="children"),
        Output(component_id="AchivementSum", component_property="children"),
        Output(component_id="Asm", component_property="figure"),
        Output(component_id="SalesOfficerr", component_property="figure"),
        Output(component_id="Asoo", component_property="figure"),
        Output(component_id="FieldOfficerNamee", component_property="figure"),
    ],
    [
        Input(component_id="MonthFilter", component_property="value"),
        Input(component_id="resetPies", component_property="n_clicks"),
        Input(component_id="Asm", component_property="clickData"),
        Input(component_id="SalesOfficerr", component_property="clickData"),
        Input(component_id="Asoo", component_property="clickData"),
        Input(component_id="FieldOfficerNamee", component_property="clickData"),
    ],
)
def updateGraphs(MonthStatus,resetPies, Asm, SalesOfficer, Aso, FieldOfficerName):
    if not any([MonthStatus, Asm, SalesOfficer, Aso, FieldOfficerName]):
        filteredDataFrame = df
        return createGraphs(filteredDataFrame)
    else:
        MonthStatusMask = df["Month"].isin(MonthStatus) if MonthStatus else True
        AsmMask = df["Asm"] == Asm["points"][0]["label"] if Asm else True
        SalesOfficerMask = (
            df["SalesOfficer"] == SalesOfficer["points"][0]["x"]
            if SalesOfficer
            else True
        )
        AsoMask = df["Aso"] == Aso["points"][0]["x"] if Aso else True
        FieldOfficerMask = (
            df["FieldOfficerName"] == FieldOfficerName["points"][0]["x"]
            if FieldOfficerName
            else True
        )
        filteredDataFrame = df[
            MonthStatusMask & AsmMask & SalesOfficerMask & AsoMask & FieldOfficerMask
        ]

        return createGraphs(filteredDataFrame)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
