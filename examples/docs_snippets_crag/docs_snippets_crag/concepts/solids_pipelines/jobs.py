from dagster import ResourceDefinition, graph, op


@op(config_schema={"number": int}, required_resource_keys={"my_resource"})
def do_something(context):
    context.log.info("number: " + context.op_config["number"])
    context.log.info("my_resource: " + context.resources.my_resource)


@graph
def do_it_all():
    do_something()


do_it_all_job = do_it_all.to_job(
    run_config={"ops": {"do_something": {"config": {"number": 5}}}},
    resource_defs={"my_resource": ResourceDefinition.string_resource("hello")},
)
