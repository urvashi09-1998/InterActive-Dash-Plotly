import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, callback, Dash
from pymongo import MongoClient
from dash.dependencies import Input, Output

user = "ip2pdb"
pwd = "indiap2pdb"
client = MongoClient(
    f'mongodb://{user}:{pwd}@10.0.15.7:17071/?authMechanism=DEFAULT&authSource=indiaP2P'
)
db="indiaP2P"
# db = "indiaP2P-uat"
collection = "loantickets"

pipeline = [
    {
        '$lookup': {
            'from': 'partners',
            'localField': 'partnerId',
            'foreignField': '_id',
            'as': 'partnerDetails'
        }
    }, {
        '$unwind': {
            'path': '$partnerDetails'
        }
    }, {
        '$project': {
            'loanStatus': 1,
            'debt': '$creditResponse.totalIndebtedness',
            'dues': '$creditResponse.totalPastDue',
            'earningMembers': {
                '$toInt': '$borrowerDetail.incomeDetails.noOfEarningMembers'
            },
            'mfi': '$creditResponse.scores.mfiScore',
            'retail': '$creditResponse.scores.retailScore',
            'houseOwnership': '$borrowerDetail.assetsInfo.isHouseOwned',
            'employmentDuration': {
                '$toInt': '$borrowerDetail.employmentInfo.employmentDuration'
            },
            'houseType': '$borrowerDetail.assetsInfo.houseType',
            'noOfIncomeSources': {
                '$cond': {
                    'if': {
                        '$eq': [
                            {
                                '$type': '$borrowerDetail.incomeDetails.noOfIncomeSources'
                            }, 'string'
                        ]
                    },
                    'then': {
                        '$convert': {
                            'input': {
                                '$trim': {
                                    'input': '$borrowerDetail.incomeDetails.noOfIncomeSources'
                                }
                            },
                            'to': 'int'
                        }
                    },
                    'else': {
                        '$toInt': '$borrowerDetail.incomeDetails.noOfIncomeSources'
                    }
                }
            },
            'noOfFamilyMembers': {
                '$cond': {
                    'if': {
                        '$eq': [
                            {
                                '$type': '$borrowerDetail.incomeDetails.noOfFamilyMembers'
                            }, 'string'
                        ]
                    },
                    'then': {
                        '$convert': {
                            'input': {
                                '$trim': {
                                    'input': '$borrowerDetail.incomeDetails.noOfFamilyMembers'
                                }
                            },
                            'to': 'int'
                        }
                    },
                    'else': {
                        '$toInt': '$borrowerDetail.incomeDetails.noOfFamilyMembers'
                    }
                }
            },
            'netIncome': {
                '$cond': {
                    'if': {
                        '$eq': [
                            {
                                '$type': '$borrowerDetail.incomeDetails.familyMonthlyIncome'
                            }, 'string'
                        ]
                    },
                    'then': {
                        '$toInt': {
                            '$trim': {
                                'input': {
                                    '$replaceAll': {
                                        'input': '$borrowerDetail.incomeDetails.familyMonthlyIncome',
                                        'find': ',',
                                        'replacement': ''
                                    }
                                }
                            }
                        }
                    },
                    'else': '$borrowerDetail.incomeDetails.familyMonthlyIncome'
                }
            },
            'partnerScore': {
                '$toDouble': '$partnerDetails.partnerScore'
            },
            'partnerName': '$partnerDetails.partnerName'
        }
    }
]

projectedDataFrame = pd.DataFrame(list(client[db][collection].aggregate(pipeline)))

# Styling.
colorScheme = px.colors.sequential.Bluyl_r
fontStyle = dict(family="Times New Roman")

# Filling null values.
projectedDataFrame["mfi"] = projectedDataFrame["mfi"].fillna(0)
projectedDataFrame["retail"] = projectedDataFrame["retail"].fillna(0)
projectedDataFrame["houseType"] = projectedDataFrame["houseType"].fillna(
    "Data unavailable"
)
projectedDataFrame["dues"] = projectedDataFrame["dues"].fillna(0)

# Dues Rectification.
for i, val in enumerate(projectedDataFrame["dues"]):
    if val >= 5:
        projectedDataFrame.at[i, "dues"] = "More than 5"

# Debt rectification.
projectedDataFrame["debt"] = projectedDataFrame["debt"].fillna(0)
projectedDataFrame["debt"] = projectedDataFrame["debt"] / 100
bins = [-float('inf'), 0, 1, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, float('inf')]
labels = ['No Data', '0', '1-500', '500-1k', '1k-2k', '2k-3k', '3k-4k', '4k-5k', '5k-6k', '6k-7k', '7k-8k', '8k-9k', '9k-10k',
          'More than 10k']
projectedDataFrame["Amount of Debt"] = pd.cut(
    projectedDataFrame["debt"], bins=bins, labels=labels
)

# Net Income Rectification.
bins = [-5, 0, 25000, 35000, 45000, 55000, 65000, 80000, 95000, 110000, float("inf")]
labels = ["No Data", "0-25k", "25k-35k", "35k-45k", "45k-55k", "55k-65k", "65k-80k", "80k-95k", "95k-1.1L",
          "More than 1.1L"]
projectedDataFrame["familyIncome"] = pd.cut(
    projectedDataFrame["netIncome"], bins=bins, labels=labels
)

# Employment Duration Rectification.
for i, val in enumerate(projectedDataFrame["employmentDuration"]):
    if 2 >= val >= 0:
        projectedDataFrame.at[i, "duration"] = "0-2"
    elif 5 >= val >= 2:
        projectedDataFrame.at[i, "duration"] = "2-5"
    elif 8 >= val >= 6:
        projectedDataFrame.at[i, "duration"] = "6-8"
    elif 10 >= val >= 8:
        projectedDataFrame.at[i, "duration"] = "8-10"
    elif 15 >= val >= 11:
        projectedDataFrame.at[i, "duration"] = "11-15"
    elif 20 >= val >= 16:
        projectedDataFrame.at[i, "duration"] = "16-20"
    elif 25 >= val >= 21:
        projectedDataFrame.at[i, "duration"] = "21-25"
    elif 30 >= val >= 26:
        projectedDataFrame.at[i, "duration"] = "26-30"
    elif 35 >= val >= 31:
        projectedDataFrame.at[i, "duration"] = "31-35"
    else:
        projectedDataFrame.at[i, "duration"] = "More than 35"

# MFI Score Rectification.
bins = [-float("inf"), 0, 100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900]
labels = ['Data Unavailable', '0-100', '100-200', '200-300', '300-400', '400-500', '500-600', '600-700', '700-750',
          '750-800', '800-850', '850-900']
projectedDataFrame["mfi"] = pd.cut(projectedDataFrame["mfi"], bins=bins, labels=labels)

# Retail Score Rectification.
bins = [-float("inf"), 0, 100, 200, 300, 400, 500, 600, 700, 750, 800, 850, 900]
labels = ['Data Unavailable', '0-100', '100-200', '200-300', '300-400', '400-500', '500-600', '600-700', '700-750',
          '750-800', '800-850', '850-900']
projectedDataFrame["retail"] = pd.cut(
    projectedDataFrame["retail"], bins=bins, labels=labels
)

# House Type Rectification.
projectedDataFrame["houseType"] = projectedDataFrame["houseType"].fillna(
    "Data Unavailable"
)

# Family Member Rectification.
for i, val in enumerate(projectedDataFrame["noOfFamilyMembers"]):
    if 1 >= val >= 0:
        projectedDataFrame.at[i, "family"] = "0-1"
    elif 3 >= val >= 2:
        projectedDataFrame.at[i, "family"] = "2-4"
    elif 5 >= val >= 4:
        projectedDataFrame.at[i, "family"] = "4-5"
    elif 7 >= val >= 6:
        projectedDataFrame.at[i, "family"] = "6-7"
    else:
        projectedDataFrame.at[i, "family"] = "More than 7"

# Partner Rectification.
for i, val in enumerate(projectedDataFrame["partnerName"]):
    if val == "Velicham Finance Private Limited":
        projectedDataFrame.at[i, 'partnerScore'] = 26.13
    elif val == "test":
        projectedDataFrame.at[i, 'partnerScore'] = 15
    elif val == "ACTS MAHILA MUTUALLY AIDED CO- OPERATIVE THRIFT SOCIETY  (AMMACTS)":
        projectedDataFrame.at[i, 'partnerScore'] = 24.29
    elif val == "ARUL FINANCIERS PRIVATE LIMITED":
        projectedDataFrame.at[i, 'partnerScore'] = 23.96
    elif val == "DDSolar":
        projectedDataFrame.at[i, 'partnerScore'] = 25
    elif val == "M/s I Yanchu Chang-ECS":
        projectedDataFrame.at[i, 'partnerScore'] = 0.01
    elif val == "M/s EASYOWN-RBN":
        projectedDataFrame.at[i, 'partnerScore'] = 0
    elif val == "Pradakshana Fintech Pvt Ltd":
        projectedDataFrame.at[i, 'partnerScore'] = 23.95
    elif val == "MAXIMAL FINANCE AND INVESTMENT LIMITED":
        projectedDataFrame.at[i, 'partnerScore'] = 27
    elif val == "Bargach Finance Private Limited":
        projectedDataFrame.at[i, 'partnerScore'] = 22.96
    elif val == "Padma Procred Private Limited":
        projectedDataFrame.at[i, 'partnerScore'] = 'Score not assigned'
    elif val == "Vector Finance Private limited":
        projectedDataFrame.at[i, 'partnerScore'] = 21.46

for i, val in enumerate(projectedDataFrame["partnerName"]):
    if val == "ACTS MAHILA MUTUALLY AIDED CO- OPERATIVE THRIFT SOCIETY  (AMMACTS)":
        projectedDataFrame.at[i, 'partnerName'] = 'AMMACTS'

projectedDataFrame['partnerScore'] = projectedDataFrame['partnerScore'].fillna('Score not assigned')
projectedDataFrame[['dues', 'noOfIncomeSources', 'earningMembers']] = projectedDataFrame[['dues', 'noOfIncomeSources', 'earningMembers']].astype(str).round(0)


def createGraphs(dataFrame):
    colorScheme = px.colors.sequential.Bluyl_r
    fontStyle = dict(family="Times New Roman")

    # Past Dues.
    duesPie = px.pie(
        data_frame=dataFrame,
        names=dataFrame["dues"].value_counts().index,
        values=dataFrame["dues"].value_counts(),
        hole=0.4,
        color_discrete_sequence=colorScheme,
    )
    duesPie.update_traces(
        textinfo="percent",
        textposition="auto",
        automargin=True,
        marker={"line": {"width": 0.5, "color": "black"}},
    )
    duesPie.update_layout(
        font=fontStyle,
        paper_bgcolor="#F5F5F5",
        title="Total Past Dues",
        clickmode='event',
        legend=dict(title_text="No of dues", x=0.85, font=dict(size=15)),
        title_x=0.5,
    )

    # Total Debt.
    # debtFrame = (
    #     dataFrame.groupby(dataFrame["Amount of Debt"])["Amount of Debt"]
    #     .count()
    #     .rename("count")
    #     .to_frame()
    # )
    debtPercentage = (
        (
                (
                        dataFrame["Amount of Debt"].value_counts()
                        / dataFrame["_id"].count()
                )
                * 100
        ).round(2)
    ).astype(str)
    # debtArea = px.area(
    #     data_frame=debtFrame,
    #     y="count",
    #     color_discrete_sequence=colorScheme,
    #     markers=True,
    #     title="Debt Distribution",
    # )

    debtArea = px.bar(
        data_frame=dataFrame,
        x=dataFrame["Amount of Debt"].value_counts().index,
        y=dataFrame["Amount of Debt"].value_counts(),
        labels={"x": "Total Debt", "y": "No of People"},
        text=debtPercentage,
        title="No of Income Sources",
        color_discrete_sequence=colorScheme,
    )
    debtArea.update_traces(
        textposition="auto", marker={"line": {"width": 2, "color": "black"}}
    )
    debtArea.update_layout(
        font=fontStyle,
        title="Debt Distribution",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        clickmode='event+select',
        xaxis={'categoryorder': 'category ascending'},
        xaxis_title="Amount of Debt",
        yaxis_title="No of People",
    )

    # Net family income.
    # incomeFrame = (
    #     dataFrame.groupby(dataFrame["familyIncome"])["familyIncome"]
    #     .count()
    #     .rename("count")
    #     .to_frame()
    # )
    incomePercentage = (
        (
                (
                        dataFrame["familyIncome"].value_counts()
                        / dataFrame["_id"].count()
                )
                * 100
        ).round(2)
    ).astype(str)
    # netIncomeArea = px.area(
    #     data_frame=incomeFrame,
    #     y="count",
    #     markers=True,
    #     title="Income Distribution",
    #     color_discrete_sequence=colorScheme,
    # )
    netIncomeArea = px.bar(
        data_frame=dataFrame,
        x=dataFrame["familyIncome"].value_counts().index,
        y=dataFrame["familyIncome"].value_counts(),
        labels={"x": "Total Family Income", "y": "No of People"},
        text=incomePercentage,
        title="No of Income Sources",
        color_discrete_sequence=colorScheme,
    )
    netIncomeArea.update_traces(
        textposition="auto", marker={"line": {"width": 2, "color": "black"}}
    )
    netIncomeArea.update_layout(
        font=fontStyle,
        title="Income Distribution",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        clickmode='event+select',
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="Total Family Income",
        yaxis_title="No of People",
    )

    # Income Sources.
    incomeSourcesPercentage = (
        (
                (
                        dataFrame["noOfIncomeSources"].value_counts()
                        / dataFrame["_id"].count()
                )
                * 100
        )
        .round(2)
        .astype(str)
    )

    incomeSourcesBar = px.bar(
        data_frame=dataFrame,
        x=dataFrame["noOfIncomeSources"].value_counts().index,
        y=dataFrame["noOfIncomeSources"].value_counts(),
        labels={"x": "No of Income Sources", "y": "No of People"},
        text=incomeSourcesPercentage,

        title="No of Income Sources",
        color_discrete_sequence=colorScheme,
    )
    incomeSourcesBar.update_layout(
        font=fontStyle,
        title="Distribution of Income Sources",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        clickmode='event+select',
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="No of Income Sources",
        yaxis_title="No of People",
    )
    incomeSourcesBar.update_traces(
        textposition="auto", marker={"line": {"width": 2, "color": "black"}}
    )

    # Earning Members.
    earnMemPercentage = (
        (
                (
                        dataFrame["earningMembers"].value_counts()
                        / dataFrame["_id"].count()
                )
                * 100
        )
        .round(2)
        .astype(str)
    )

    earningMembersBar = px.bar(
        data_frame=dataFrame,
        x=dataFrame["earningMembers"].value_counts().index,
        y=dataFrame["earningMembers"].value_counts(),
        text=earnMemPercentage,
        labels={"x": "No of Earning Members", "y": "No of People"},
        title="No of Earning Members",
        color_discrete_sequence=colorScheme,
    )

    earningMembersBar.update_layout(
        font=fontStyle,
        title="Distribution of Earning Members",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        clickmode='event+select',
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="No of Earning Members",
        yaxis_title="No of People",
    )
    earningMembersBar.update_traces(
        textposition="auto", marker={"line": {"width": 2, "color": "black"}}
    )

    # Employment Duration.
    employmentPie = px.pie(
        data_frame=dataFrame,
        names=dataFrame["duration"].value_counts().index,
        values=dataFrame["duration"].value_counts(),
        color_discrete_sequence=colorScheme,
    )
    employmentPie.update_traces(
        textinfo="percent",
        textposition="auto",
        automargin=True,
        marker={"line": {"width": 0.5, "color": "black"}},
    )
    employmentPie.update_layout(
        font=fontStyle,
        paper_bgcolor="#F5F5F5",
        title="Employment Duration",
        legend=dict(title_text="Years", x=0.85, font=dict(size=15)),
        title_x=0.5,
    )

    # MFI Score.
    mfiPie = px.pie(
        data_frame=dataFrame,
        names=dataFrame["mfi"].value_counts().index,
        values=dataFrame["mfi"].value_counts(),
        color_discrete_sequence=colorScheme,
        title="MFI",
    )
    mfiPie.update_traces(
        textinfo="percent",
        textposition="auto",
        automargin=True,
        marker={"line": {"width": 0.5, "color": "black"}},
    )
    mfiPie.update_layout(
        font=fontStyle,
        paper_bgcolor="#F5F5F5",
        title="Distribution of Scores (MFI)",
        legend=dict(title_text="MFI Score", x=0.85, font=dict(size=15)),
        title_x=0.5,
    )

    # Retail Score.
    retailPie = px.pie(
        data_frame=dataFrame,
        names=sorted(dataFrame["retail"].value_counts().index),
        values=sorted(dataFrame["retail"].value_counts()),
        color_discrete_sequence=colorScheme,
        title="Retail",
    )
    retailPie.update_traces(
        textinfo="percent",
        textposition="auto",
        automargin=True,
        marker={"line": {"width": 0.5, "color": "black"}},
    )
    retailPie.update_layout(
        font=fontStyle,
        paper_bgcolor="#F5F5F5",
        title="Distribution of Scores (Retail)",
        legend=dict(title_text="Retail Score", x=0.85, font=dict(size=15)),
        title_x=0.5,
    )

    # House Ownership.
    houseOwnershipPercentage = (
        (
                (
                        dataFrame["houseOwnership"].value_counts()
                        / dataFrame["_id"].count()
                )
                * 100
        )
        .round(2)
        .astype(str)
    )
    houseOwnershipBar = px.bar(
        data_frame=dataFrame,
        x=dataFrame["houseOwnership"].value_counts().index,
        y=dataFrame["houseOwnership"].value_counts(),
        color_discrete_sequence=colorScheme,
        text=houseOwnershipPercentage,
        title="House Ownership",
        labels={"x": "Status", "y": "No of People"},
    )
    houseOwnershipBar.update_layout(
        font=fontStyle,
        title="House Ownership",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        clickmode='event+select',
        xaxis={"categoryorder": "category ascending"},
        xaxis_title="Status",
        yaxis_title="No of People",
    )
    houseOwnershipBar.update_traces(
        textposition="auto", marker={"line": {"width": 2, "color": "black"}}
    )

    # House Type.
    houseTypePie = px.pie(
        data_frame=dataFrame,
        names=dataFrame["houseType"].value_counts().index,
        values=dataFrame["houseType"].value_counts(),
        color_discrete_sequence=colorScheme,
        title="House Type",
        hole=0.4,
    )
    houseTypePie.update_traces(
        textinfo="percent",
        textposition="auto",
        automargin=True,
        marker={"line": {"width": 0.5, "color": "black"}},
    )
    houseTypePie.update_layout(
        font=fontStyle,
        paper_bgcolor="#F5F5F5",
        title="Distribution of House Type",
        legend=dict(title_text="House Type", x=0.85, font=dict(size=15)),
        title_x=0.5,
    )

    # No of Family Members.
    familyMembersPie = px.pie(
        data_frame=dataFrame,
        names=dataFrame["family"].value_counts().index,
        values=dataFrame["family"].value_counts(),
        color_discrete_sequence=colorScheme,
        hole=0.4,
    )
    familyMembersPie.update_traces(
        textinfo="percent",
        textposition="auto",
        automargin=True,
        marker={"line": {"width": 0.5, "color": "black"}},
    )
    familyMembersPie.update_layout(
        font=fontStyle,
        paper_bgcolor="#F5F5F5",
        title="Distribution of Family Members",
        legend=dict(title_text="No of Members", x=0.85, font=dict(size=15)),
        title_x=0.5,
    )

    # Loan Status.
    loanStatusDisplay = (
            (dataFrame['loanStatus'].value_counts() / dataFrame['_id'].count()) * 100).round(
        2).astype(str)

    statusBar = px.bar(data_frame=dataFrame,
                       x=dataFrame['loanStatus'].unique(),
                       y=dataFrame['loanStatus'].value_counts(),
                       text=loanStatusDisplay,
                       labels={'x': 'Loan Status', 'y': 'No of Loans'},
                       color_discrete_sequence=colorScheme)
    statusBar.update_layout(
        font=fontStyle,
        title="Loan Status",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        # xaxis={"categoryorder": "category ascending"},
        xaxis_title="Status",
        yaxis_title="No of Loans",
    )
    statusBar.update_traces(textposition="auto", marker={"line": {"width": 2, "color": "black"}})

    # Partner Score.
    partnerPercentageDisplay = (
            (dataFrame['partnerName'].value_counts() / dataFrame['_id'].count()) * 100).round(
        2).astype(str)
    partnerScoreBar = px.bar(data_frame=dataFrame,
                             y=dataFrame['partnerName'].value_counts().index,
                             x=dataFrame['partnerName'].value_counts(),
                             hover_name=dataFrame['partnerScore'].value_counts().index,
                             text= partnerPercentageDisplay,
                             orientation='h',
                             color_discrete_sequence=colorScheme,
                             height=500,
                             labels={'y': 'Partner Name', 'x': 'No of Loans'},
                             )

    partnerScoreBar.update_layout(
        font=fontStyle,
        title="Partner",
        title_x=0.5,
        plot_bgcolor="#F5F5F5",
        paper_bgcolor="#F5F5F5",
        clickmode='event+select',
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="No of Loans",
        yaxis_title="Partner Name",
    )
    partnerScoreBar.update_traces(textposition="auto", marker={"line": {"width": 2, "color": "black"}})

    return (
        f"No of Loans: {dataFrame['_id'].count()}",
        f"Percentage of Loans: {((dataFrame['_id'].count()/projectedDataFrame['_id'].count())*100).round(2)}%",
        duesPie,
        debtArea,
        netIncomeArea,
        incomeSourcesBar,
        earningMembersBar,
        employmentPie,
        mfiPie,
        retailPie,
        houseOwnershipBar,
        houseTypePie,
        familyMembersPie,
        statusBar,
        partnerScoreBar,
    )


app = dash.Dash(__name__)
app.layout = html.Div(
    [
        html.H1(
            "Loans Dashboard",
            style={"fontSize": 30, "textAlign": "center"},
        ),
        html.Div(
            dcc.Dropdown(
                id="statusFilter",
                placeholder="Select Loan Status",
                style={"width": "100%"},
                options=sorted(projectedDataFrame['loanStatus'].unique()),
                multi=True,
            )
        ),
        html.Hr(),
        html.Div([html.Div(id='netLoans', style={'width': '100%', "textAlign": "center"}),
                  html.Button('Reset Pie Charts', id='resetPies', style={'width': '100%'}),
                  html.Div(id='netLoansPercentage', style={'width': '100%', "textAlign": "center"}),
                  ], style={"display": "flex", "flex-direction": "row"}),
        html.Div(
            [
                dcc.Graph(id="pastDues", style={"width": "100%"}),
                dcc.Graph(id="totalDebt", style={"width": "100%"}, animate=True),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="netIncome", style={"width": "100%"}, animate=True),
                dcc.Graph(id="incomeSources", style={"width": "100%"}, animate=True),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="earningMembers", style={"width": "100%"}, animate=True),
                dcc.Graph(id="employmentDuration", style={"width": "100%"}),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="mfi", style={"width": "100%"}),
                dcc.Graph(id="retail", style={"width": "100%"}),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="houseOwnership", style={"width": "100%"}, animate=True),
                dcc.Graph(id="houseType", style={"width": "100%"}),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="familyMembers", style={"width": "100%"}),
                dcc.Graph(id="loanStatus", style={"width": "100%"}, animate=True),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.Div(
            [
                dcc.Graph(id="partnerScore", style={"width": "100%"}, animate=True),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
    ]
)


@callback(
    [
        Output(component_id="netLoans", component_property="children"),
        Output(component_id="netLoansPercentage", component_property="children"),
        Output(component_id="pastDues", component_property="figure"),
        Output(component_id="totalDebt", component_property="figure"),
        Output(component_id="netIncome", component_property="figure"),
        Output(component_id="incomeSources", component_property="figure"),
        Output(component_id="earningMembers", component_property="figure"),
        Output(component_id="employmentDuration", component_property="figure"),
        Output(component_id="mfi", component_property="figure"),
        Output(component_id="retail", component_property="figure"),
        Output(component_id="houseOwnership", component_property="figure"),
        Output(component_id="houseType", component_property="figure"),
        Output(component_id="familyMembers", component_property="figure"),
        Output(component_id="loanStatus", component_property="figure"),
        Output(component_id="partnerScore", component_property="figure"),
    ],
    [
        Input(component_id="statusFilter", component_property="value"),
        Input(component_id="resetPies", component_property="n_clicks"),
        Input(component_id="pastDues", component_property="clickData"),
        Input(component_id="totalDebt", component_property="selectedData"),
        Input(component_id="netIncome", component_property="selectedData"),
        Input(component_id="incomeSources", component_property="selectedData"),
        Input(component_id="earningMembers", component_property="selectedData"),
        Input(component_id="employmentDuration", component_property="clickData"),
        Input(component_id="mfi", component_property="clickData"),
        Input(component_id="retail", component_property="clickData"),
        Input(component_id="houseOwnership", component_property="selectedData"),
        Input(component_id="houseType", component_property="clickData"),
        Input(component_id="familyMembers", component_property="clickData"),
        Input(component_id="partnerScore", component_property="selectedData"),
    ],
)
def updateGraphs(loanStatus, resetPies, clickDataDues, clickDataDebt, clickDataNetIncome, clickDataIncomeSources, clickDataEarningMembers, clickDataEmploymentDuration,
                 clickDataMFI, clickDataRetail, clickDataHouseOwnership, clickDataHouseType, clickDataFamilyMembers, clickDataPartnerScore):

    if not any([loanStatus, clickDataDues, clickDataDebt, clickDataNetIncome, clickDataIncomeSources, clickDataEarningMembers, clickDataEmploymentDuration,
                 clickDataMFI, clickDataRetail, clickDataHouseOwnership, clickDataHouseType, clickDataFamilyMembers, clickDataPartnerScore]):
        filteredDataFrame = projectedDataFrame
        return createGraphs(filteredDataFrame)
    else:
        loanStatusMask = projectedDataFrame['loanStatus'].isin(loanStatus) if loanStatus else True
        duesMask = projectedDataFrame['dues'] == clickDataDues['points'][0]['label'] if clickDataDues else True
        debtMask = projectedDataFrame['Amount of Debt'] == clickDataDebt['points'][0]['label'] if clickDataDebt else True
        incomeMask = projectedDataFrame['familyIncome'] == clickDataNetIncome['points'][0]['label'] if clickDataNetIncome else True
        incomeSourcesMask = projectedDataFrame['noOfIncomeSources'] == clickDataIncomeSources['points'][0]['label'] if clickDataIncomeSources else True
        earningMembersMask = projectedDataFrame['earningMembers'] == clickDataEarningMembers['points'][0]['label'] if clickDataEarningMembers else True
        employmentDurationMask = projectedDataFrame['duration'] == clickDataEmploymentDuration['points'][0]['label'] if clickDataEmploymentDuration else True
        MFIScoreMask = projectedDataFrame['mfi'] == clickDataMFI['points'][0]['label'] if clickDataMFI else True
        retailScoreMask = projectedDataFrame['retail'] == clickDataRetail['points'][0]['label'] if clickDataRetail else True
        houseOwnershipMask = projectedDataFrame['houseOwnership'] == clickDataHouseOwnership['points'][0]['label'] if clickDataHouseOwnership else True
        houseTypeMask = projectedDataFrame['houseType'] == clickDataHouseType['points'][0]['label'] if clickDataHouseType else True
        familyMembersMask = projectedDataFrame['family'] == clickDataFamilyMembers['points'][0]['label'] if clickDataFamilyMembers else True
        partnerNameMask = projectedDataFrame['partnerName'] == clickDataPartnerScore['points'][0]['label'] if clickDataPartnerScore else True
        filteredDataFrame = projectedDataFrame[loanStatusMask & duesMask & debtMask & incomeMask & incomeSourcesMask
                                               & earningMembersMask & employmentDurationMask & MFIScoreMask & retailScoreMask & houseOwnershipMask
                                               & houseTypeMask & familyMembersMask & partnerNameMask]
        print(filteredDataFrame[['dues', 'mfi', 'retail']])
        print(filteredDataFrame['retail'].value_counts().index)
        # if resetPies >= 1:
        #     print(resetPies)
        #     duesMask = employmentDurationMask = MFIScoreMask = retailScoreMask = houseTypeMask = familyMembersMask = True
        #     filteredDataFrame = projectedDataFrame[loanStatusMask & duesMask & debtMask & incomeMask & incomeSourcesMask
        #                                            & earningMembersMask & employmentDurationMask & MFIScoreMask & retailScoreMask & houseOwnershipMask
        #                                            & houseTypeMask & familyMembersMask & partnerNameMask]
        #     print(filteredDataFrame[
        #               ['loanStatus', 'dues', 'Amount of Debt', 'familyIncome', 'noOfIncomeSources', 'earningMembers',
        #                'mfi', 'retail']])
        #
        # else:
        #     print(resetPies)
        #     filteredDataFrame = projectedDataFrame[loanStatusMask & duesMask & debtMask & incomeMask & incomeSourcesMask
        #                                            & earningMembersMask & employmentDurationMask & MFIScoreMask & retailScoreMask & houseOwnershipMask
        #                                            & houseTypeMask & familyMembersMask & partnerNameMask]
        #     print(filteredDataFrame[
        #               ['loanStatus', 'dues', 'Amount of Debt', 'familyIncome', 'noOfIncomeSources', 'earningMembers',
        #                'mfi', 'retail']])

        return createGraphs(filteredDataFrame)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
