import weaviate


def create_weaviate_client():
    return weaviate.connect_to_local()


def create_async_weaviate_client():
    return weaviate.use_async_with_local()


def disconnect_weaviate_client(client):
    client.close()
