import weaviate


def create_weaviate_client():
    return weaviate.connect_to_local()

def disconnect_weaviate_client(client):
    client.close()
