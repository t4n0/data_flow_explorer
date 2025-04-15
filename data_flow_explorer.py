import argparse
import collections
import graphviz as gv
import json
import jsonschema
import streamlit as sl
import tempfile

COMPONENT = "component"
INPUTS = "inputs"
OUTPUTS = "outputs"


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise Exception(f'Command line argument parser failed with "{message}".')


def parse_command_line_arguments():
    parser = ThrowingArgumentParser(
        description="data flow explorer", exit_on_error=False
    )
    parser.add_argument(
        "--input_file",
        required=True,
        help="Full path to the file specifying the data flow of the entire system.",
    )
    return parser.parse_args()


def read(file_path: str):
    with open(file_path, "r") as file_handle:
        content = json.load(file_handle)
    return content


def validate(data_flow: dict, file_path: str):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                COMPONENT: {"type": "string"},
                INPUTS: {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
                OUTPUTS: {
                    "type": "array",
                    "items": {"type": "string"},
                    "uniqueItems": True,
                },
            },
            "required": [COMPONENT, INPUTS, OUTPUTS],
            "additionalProperties": False,
        },
    }

    try:
        jsonschema.validate(instance=data_flow, schema=schema)
    except jsonschema.exceptions.ValidationError as error:
        raise Exception(
            f'Input file "{file_path}" failed validation. Schema violated. '
            + str(error)
        )

    all_components = [item[COMPONENT] for item in data_flow]
    all_data = {
        datum for item in data_flow for datum in [*item[INPUTS], *item[OUTPUTS]]
    }
    repeated_components = [
        component
        for component, count in collections.Counter(all_components).items()
        if count > 1
    ]
    ambiguous_names = [item for item in all_components if item in all_data]

    if any(component == "" for component in all_components):
        raise Exception(
            f'Input file "{file_path}" failed validation. Component names must not be empty strings.'
        )
    if any(datum == "" for datum in all_data):
        raise Exception(
            f'Input file "{file_path}" failed validation. Data names must not be empty strings.'
        )
    if repeated_components:
        raise Exception(
            f'Input file "{file_path}" failed validation. Component names must be unique. These names appear more than once: {repeated_components}.'
        )
    if ambiguous_names:
        raise Exception(
            f'Input file "{file_path}" failed validation. Data and component names must not be mixed. These names appear both as a component and a data name: {ambiguous_names}.'
        )

    return


def create_digraph():
    graph_attributes = {"rankdir": "LR", "bgcolor": "#0E1117"}
    node_attributes = {
        "fontcolor": "#e6e6e6",
        "style": "filled",
        "color": "#e6e6e6",
        "fillcolor": "#333333",
    }
    edge_attributes = {"color": "#e6e6e6", "fontcolor": "#e6e6e6"}
    return gv.Digraph(
        format="svg",
        graph_attr=graph_attributes,
        node_attr=node_attributes,
        edge_attr=edge_attributes,
    )


def visualize_graph(visualized_options: list, data_flow: dict):
    G = create_digraph()
    for item in data_flow:
        if item[COMPONENT] in visualized_options:
            G.node(item[COMPONENT], shape="box", color="magenta")
            for input in item[INPUTS]:
                if input in visualized_options:
                    G.node(input, shape="ellipse", color="cyan")
                    G.edge(input, item[COMPONENT])
            for output in item[OUTPUTS]:
                if output in visualized_options:
                    G.node(output, shape="ellipse", color="cyan")
                    G.edge(item[COMPONENT], output)
    with tempfile.TemporaryDirectory() as temporary_directory:
        sl.image(G.render(directory=temporary_directory), use_container_width=True)


def visualize(data_flow: dict, file_path: str):
    all_options = sorted(
        {
            name
            for item in data_flow
            for name in [item[COMPONENT], *item[INPUTS], *item[OUTPUTS]]
        }
    )

    sl.title("data flow explorer")
    tab_partial, tab_full, tab_legend, tab_input_file = sl.tabs(
        ["partial graph", "full graph", "legend", "input file"]
    )

    with tab_partial:
        selected_options = set(
            sl.multiselect(
                label="select which component or data to visualize",
                options=all_options,
                placeholder="click to select",
            )
        )

        visualized_options = selected_options.copy()
        for item in data_flow:
            for input in item[INPUTS]:
                if item[COMPONENT] in selected_options or input in selected_options:
                    visualized_options.add(item[COMPONENT])
                    visualized_options.add(input)
            for output in item[OUTPUTS]:
                if item[COMPONENT] in selected_options or output in selected_options:
                    visualized_options.add(item[COMPONENT])
                    visualized_options.add(output)
        visualize_graph(visualized_options, data_flow)

    with tab_full:        
        visualize_graph(all_options, data_flow)

    with tab_legend:
        sl.markdown(
            '<span style="color:cyan;">Cyan</span> ellipses represent data, while <span style="color:magenta;">magenta</span> boxes represent components. Arrows show the direction of flow—pointing into components for inputs, and out of components for outputs.',
            unsafe_allow_html=True,
        )
        G = create_digraph()
        G.node("component", shape="box", color="magenta")
        G.node("input data", shape="ellipse", color="cyan")
        G.node("output data", shape="ellipse", color="cyan")
        G.edge("input data", "component")
        G.edge("component", "output data")
        with tempfile.TemporaryDirectory() as temporary_directory:
            sl.image(G.render(directory=temporary_directory), use_container_width=True)

    with tab_input_file:
        sl.text(file_path)
        sl.json(data_flow, expanded=True)


if __name__ == "__main__":
    args = parse_command_line_arguments()
    data_flow = read(args.input_file)
    validate(data_flow, args.input_file)
    visualize(data_flow, args.input_file)
