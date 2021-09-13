"""isort:skip_file"""


def some_api_call():
    return []


def train_prediction_model(_):
    return []


def persist_to_db(_):
    pass


def persist_to_model_store(_):
    pass


# start_job_0

from dagster import op, AssetKey, Out, graph


@op(out=Out(asset_key=AssetKey("my_db.users")))
def scrape_users():
    users_df = some_api_call()
    persist_to_db(users_df)
    return users_df


@op(out=Out(asset_key=AssetKey("ml_models.user_prediction")))
def get_prediction_model(users_df):
    my_ml_model = train_prediction_model(users_df)
    persist_to_model_store(my_ml_model)
    return my_ml_model


@graph
def my_user_model():
    get_prediction_model(scrape_users())


my_user_model_job = my_user_model.to_job()


# end_job_0
