from dash import Dash, Output, Input, State, html, dcc, callback, MATCH, dash_table,ctx
import dash
from dash.exceptions import PreventUpdate
import uuid
import dash_mantine_components as dmc

class TagSelectorModalAIO(dmc.Modal): 

    # A set of functions that create pattern-matching callbacks of the subcomponents
    class ids:
        # Components with these ids have to be placed outside this component:
        openBtn = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'openBtn',
            'aio_id': aio_id
        }
        selectedIdsStore = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'selectedIdsStore',
            'aio_id': aio_id
        }

        # These are the ids used in this component:
        modal = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'modal',
            'aio_id': aio_id
        }
        dataTable = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'dataTable',
            'aio_id': aio_id
        }
        selAllBtn = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'selAllBtn',
            'aio_id': aio_id
        }
        deSelAllBtn = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'deSelAllBtn',
            'aio_id': aio_id
        }
        okBtn = lambda aio_id: {
            'component': 'TagSelectorModalAIO',
            'subcomponent': 'okBtn',
            'aio_id': aio_id
        }

    # Make the ids class a public class
    ids = ids

    # Define the arguments of the All-in-One component
    def __init__(
        self,
        tagsDf,
        aio_id,
    ):
        """TagSelectorModalAIO is a component that displays a dash mantine modal
        containing a datatable for selecting tags to show in the application.

        -> For opening the modal, a button with the id TagSelectorModalAIO.ids.openBtn(aio_id) has to be placed outside the component.
        -> Since dcc.Store is reset when placed inside of modal this component also has to
            be placed outside this component. The id of the dcc.Store has to be TagSelectorModalAIO.ids.selectedIdsStore(aio_id).
        """
        # Define the component's layout
        super().__init__(
            title=dmc.Title("Select tags to show in visualizations",order=4),
            id=self.ids.modal(aio_id),
            centered=True,
            zIndex=100,
            opened=False,
            size="95%",
            children = [
                dmc.LoadingOverlay(
                    zIndex=150,
                    style={"height": "70vh","display":"flex","flex-direction":"column"},#,"overflow-y": "scroll"},
                    children=[
                        dash_table.DataTable(
                            id=self.ids.dataTable(aio_id),
                            columns=[
                                {"name": i, "id": i, "deletable": False, "selectable": False} for i in tagsDf.columns
                            ],
                            data=tagsDf.to_dict('records'),
                            editable=False,
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            # column_selectable="single",
                            row_selectable="multi",
                            row_deletable=False,
                            # selected_row_ids=[],
                            # selected_rows=[],
                            # page_action="native",
                            # page_current= 0,
                            # page_size= 20,
                            # fixed_rows={ 'headers': True},
                            # virtualization=True,
                            # style={'flex':'1 1 10%'}, # Property not available: Outer container style had to be
                            # set by dash-table-container class (Sets style for all tables
                            # in the app!!) to avoid overflow of the table.
                            style_table={'overflowX': 'scroll','overflowY': 'scroll','height': '100%'},
                        ),
                    dmc.Group(
                        mt=20,
                        children=[
                            dmc.Button(
                                "Select all (filtered) rows",
                                id=self.ids.selAllBtn(aio_id),
                            ),
                            dmc.Button(
                                "Deselect all (filtered) rows",
                                id=self.ids.deSelAllBtn(aio_id),
                            ),
                            dmc.Space(style={"flex-grow":"1"}),
                            dmc.Button(
                                "...",
                                id=self.ids.okBtn(aio_id),
                            )
                        ]
                    ),
                    ]
                ),
                # dcc.Store(
                #     id=self.ids.selectedIdsStore(aio_id),
                #     storage_type="local",
                # ),
            ]
        )


    # Row selection buttons (see https://stackoverflow.com/a/66985673)
    # @callback(
    #     [Output(ids.dataTable(MATCH), 'selected_rows')],
    #     [
    #         Input(ids.selAllBtn(MATCH), 'n_clicks'),
    #         Input(ids.deSelAllBtn(MATCH), 'n_clicks')
    #     ],
    #     [
    #         State(ids.dataTable(MATCH), 'data'),
    #         State(ids.dataTable(MATCH), 'derived_virtual_data'),
    #         State(ids.dataTable(MATCH), 'derived_virtual_selected_rows')
    #     ]
    # )
    # def select_all(select_n_clicks, deselect_n_clicks, rows, filteredRows, selected_rows):
    #     if filteredRows is not None:
    #         ctx_caller = ctx.triggered_id["subcomponent"]
    #         if ctx_caller == 'selAllBtn':
    #             selected_ids = [row for row in filteredRows]
    #             return [[i for i, row in enumerate(rows) if row in selected_ids]]
    #         if ctx_caller == 'deSelAllBtn':
    #             return [[]]
    #         raise PreventUpdate
    #     else:
    #         raise PreventUpdate
        
    @callback(
        Output(ids.okBtn(MATCH), 'children'),
        Output(ids.okBtn(MATCH), 'disabled'),

        Input(ids.dataTable(MATCH), 'derived_virtual_selected_rows'),
    )
    def update_markdown_style(selectedRows):
        if not selectedRows or len(selectedRows) == 0:
            return ["Select at least one entry!", True]
        else:
            return [f"Show data for {len(selectedRows)} tags", False]

    @callback(
        Output(ids.selectedIdsStore(MATCH), 'data'),
        Output(ids.modal(MATCH), 'opened'),
        Output(ids.dataTable(MATCH), 'selected_rows'),

        Input(ids.openBtn(MATCH), 'n_clicks'),
        Input(ids.okBtn(MATCH), 'n_clicks'),
        Input(ids.selAllBtn(MATCH), 'n_clicks'),
        Input(ids.deSelAllBtn(MATCH), 'n_clicks'),

        State(ids.dataTable(MATCH), 'data'),
        State(ids.dataTable(MATCH), 'derived_virtual_data'),
        State(ids.dataTable(MATCH), 'derived_virtual_selected_rows'),
        State(ids.selectedIdsStore(MATCH), 'data'),
        prvent_initial_call=True
    )
    def close_modal(openClicks,okClicks,selAllClicks,deSelAllClicks, rows, filteredRows,selectedRows,  selectedIds):
        # if selectedIds is None:
        #     print("Filled store!")
        #     selectedIds = [row["tagId"] for row in rows]
        #     return [selectedIds, dash.no_update, dash.no_update]

        if ctx.triggered_id is None:
            raise PreventUpdate
        
        ctx_caller = ctx.triggered_id["subcomponent"]

        # Row selection buttons (see https://stackoverflow.com/a/66985673)
        if filteredRows is not None:
            ctx_caller = ctx.triggered_id["subcomponent"]
            if ctx_caller == 'selAllBtn':
                selected_ids = [row for row in filteredRows]
                return [dash.no_update,dash.no_update,[i for i, row in enumerate(rows) if row in selected_ids]]
            if ctx_caller == 'deSelAllBtn':
                return [dash.no_update,dash.no_update,[]]


        # Open and close modal
        if ctx_caller == 'openBtn':
            # print(selectedIds)
            # print([i for i, row in enumerate(rows) if row['tagId'] in selectedIds])
            return [dash.no_update, True, [i for i, row in enumerate(rows) if row['tagId'] in selectedIds]]
        if ctx_caller == 'okBtn':
            # print(selectedRows)
            selectedTagIds = [rows[rowIdx]["tagId"] for rowIdx in selectedRows]
            return [selectedTagIds,False, dash.no_update]


        raise PreventUpdate