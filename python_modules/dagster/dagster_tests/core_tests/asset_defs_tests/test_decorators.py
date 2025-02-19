import pytest
from dagster import AssetKey, DagsterInvalidDefinitionError, SolidDefinition
from dagster.core.asset_defs import AssetIn, asset


def test_asset_no_decorator_args():
    @asset
    def my_asset():
        return 1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.output_defs) == 1
    assert len(my_asset.input_defs) == 0


def test_asset_with_inputs():
    @asset
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.output_defs) == 1
    assert len(my_asset.input_defs) == 1
    assert my_asset.input_defs[0].get_asset_key(None) == AssetKey("arg1")


def test_asset_with_inputs_and_namespace():
    @asset(namespace="my_namespace")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.output_defs) == 1
    assert len(my_asset.input_defs) == 1
    assert my_asset.input_defs[0].get_asset_key(None) == AssetKey(["my_namespace", "arg1"])


def test_asset_with_context_arg():
    @asset
    def my_asset(context):
        context.log("hello")

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.input_defs) == 0


def test_asset_with_context_arg_and_dep():
    @asset
    def my_asset(context, arg1):
        context.log("hello")
        assert arg1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.input_defs) == 1
    assert my_asset.input_defs[0].get_asset_key(None) == AssetKey("arg1")


def test_input_namespace():
    @asset(ins={"arg1": AssetIn(namespace="abc")})
    def my_asset(arg1):
        assert arg1

    assert my_asset.input_defs[0].get_asset_key(None) == AssetKey(["abc", "arg1"])


def test_input_metadata():
    @asset(ins={"arg1": AssetIn(metadata={"abc": 123})})
    def my_asset(arg1):
        assert arg1

    assert my_asset.input_defs[0].metadata == {"abc": 123}


def test_unknown_in():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(ins={"arg1": AssetIn()})
        def _my_asset():
            pass


def test_all_fields():
    @asset(
        required_resource_keys={"abc", "123"},
        io_manager_key="my_io_key",
        description="some description",
        metadata={"metakey": "metaval"},
    )
    def my_asset():
        pass

    assert my_asset.required_resource_keys == {"abc", "123"}
    assert my_asset.description == "some description"
    assert len(my_asset.output_defs) == 1
    output_def = my_asset.output_defs[0]
    assert output_def.io_manager_key == "my_io_key"
    assert output_def.metadata["metakey"] == "metaval"
