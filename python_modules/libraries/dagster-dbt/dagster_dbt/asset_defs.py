import json
import os
import subprocess
import textwrap
from typing import Any, Callable, List, Mapping, Optional

from dagster import OpDefinition, Output, SolidExecutionContext, check
from dagster.core.asset_defs import AssetIn, asset


def _load_manifest_for_project(
    project_dir: str, profiles_dir: str, select: str
) -> Mapping[str, Any]:
    command_list = [
        "dbt",
        "ls",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        profiles_dir,
        "--select",
        select,
        "--resource-type",
        "model",
    ]
    # running "dbt ls" regenerates the manifest.json, which includes a superset of the actual
    # "dbt ls" output
    subprocess.Popen(command_list, stdout=subprocess.PIPE).wait()
    manifest_path = os.path.join(project_dir, "target", "manifest.json")
    with open(manifest_path, "r") as f:
        return json.load(f)


def _get_node_name(node_info: Mapping[str, Any]):
    return "__".join([node_info["resource_type"], node_info["package_name"], node_info["name"]])


def _dbt_node_to_asset(
    node_info: Mapping[str, Any],
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
) -> OpDefinition:
    code_block = textwrap.indent(node_info["raw_sql"], "    ")
    description_sections = [
        node_info["description"],
        "#### Columns:\n" + columns_to_markdown(node_info["columns"]),
        f"#### Raw SQL:\n```\n{code_block}\n```",
    ]
    description = "\n\n".join(description_sections)

    @asset(
        name=node_info["name"],
        description=description,
        ins={
            dep_name.split(".")[-1]: AssetIn(managed=False)
            for dep_name in node_info["depends_on"]["nodes"]
        },
        required_resource_keys={"dbt"},
        io_manager_key=io_manager_key,
    )
    def _node_asset(context):
        context.resources.dbt.run(models=[".".join([node_info["package_name"], node_info["name"]])])
        if runtime_metadata_fn:
            metadata = runtime_metadata_fn(context, node_info)
            yield Output(None, metadata=metadata)

    return _node_asset


def load_assets_from_dbt(
    project_dir: Optional[str] = None,
    profiles_dir: Optional[str] = None,
    manifest_json: Optional[Mapping[str, Any]] = None,
    manifest_path: Optional[str] = None,
    select: Optional[str] = None,
    runtime_metadata_fn: Optional[
        Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]
    ] = None,
    io_manager_key: Optional[str] = None,
) -> List[OpDefinition]:
    """
    Loads a set of DBT models into Dagster assets.

    Creates one Dagster asset for each DBT model. You can point to dbt in one of few different ways:
    by setting project_dir and profiles_dir, by pointing to a manifest.json file with manifest_path,
    or by passing in a JSON-structured manifest blob into manifest_json.

    Args:
        project_dir (Optional[str]): The directory containing the DBT project to load.
        profiles_dir (Optional[str]): The profiles directory to use for loading the DBT project.
            Defaults to a directory called "config" inside the project_dir.
        select (str): A DBT selection string for the models in a project that you want to include.
            Defaults to "*".
        manifest_json (Optional[Mapping[str, Any]]): The contents of a DBT manifest.json, which contains
            a set of models to load into assets.
        manifest_path (Optional[str]): A path to a DBT manifest.json, which contains a set of models
            to load into assets.
        runtime_metadata_fn: (Optional[Callable[[SolidExecutionContext, Mapping[str, Any]], Mapping[str, Any]]]):
            A function that will be run after any of the assets are materialized and returns
            metadata entries for the asset, to be displayed in the asset catalog for that run.
        io_manager_key (Optional[str]): The IO manager key that will be set on each of the returned
            assets. When other ops are downstream of the loaded assets, the IOManager specified
            here determines how the inputs to those ops are loaded. Defaults to "io_manager_key".
    """
    if len(list(filter(None, [project_dir, manifest_json, manifest_path]))) != 1:
        check.failed(
            "Only one of the 'project_dir', 'manifest_json', and 'manifest_path' arguments should "
            "be set"
        )

    if project_dir:
        if profiles_dir is None:
            profiles_dir = project_dir + "/config"
        manifest_json_final = _load_manifest_for_project(project_dir, profiles_dir, select or "*")
    elif manifest_json:
        check.invariant(
            select is None, "'select' arg can only be provided when loading from a project dir"
        )
        manifest_json_final = manifest_json
    elif manifest_path:
        check.invariant(
            select is None, "'select' arg can only be provided when loading from a project dir"
        )
        with open(manifest_path, "r") as f:
            manifest_json_final = json.load(f)
    else:
        check.failed(
            "One of the 'project_dir', 'manifest_json', and 'manifest_path' arguments should "
            "be set, but none were."
        )

    dbt_nodes = list(manifest_json_final["nodes"].values())
    return [
        _dbt_node_to_asset(
            node_info, runtime_metadata_fn=runtime_metadata_fn, io_manager_key=io_manager_key
        )
        for node_info in dbt_nodes
        if node_info["resource_type"] == "model"
    ]


def columns_to_markdown(columns: Mapping[str, Any]) -> str:
    return (
        textwrap.dedent(
            """
        | Name | Description |
        | - | - |
    """
        )
        + "\n".join([f"| {name} | {metadata['description']}" for name, metadata in columns.items()])
    )
