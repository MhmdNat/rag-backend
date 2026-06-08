import os
import click

import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("weaviate").setLevel(logging.WARNING)


@click.group()
def cli():
    '''RAG CLI tool for PDF ingestion and querying'''
    pass

@cli.command(name="ingest")
@click.option("--source", "-s", default="data.pdf", help="Path or URL to ingest")
@click.option("--batch-size", "-b", default=500, help="Batch size for vector storage")
@click.option("--index", "-i", default="RAGDocs", help="Weaviate index/class")
@click.option("--force", "-f", is_flag=True, help="Force re-ingestion by ignoring cache")
@click.pass_context
def ingest(ctx, source, index, batch_size, force):
    if not os.path.exists(source):
        click.echo(ctx.get_help())
        raise click.ClickException(f"Missing PDF: {source}")
    from src.ingestion.ingest import ingest_pdf

    ingest_pdf(source, index, batch_size, force=force)

@cli.command(name="query")
@click.option("--query", "-q", required=True, help="Query text")
@click.option("--top-k", "-k", default=5, help="Number of top results to retrieve and rerank")
@click.option("--index", "-i", default="RAGDocs", help="Weaviate index/class")
def query(query, index, top_k):
    from src.query.query_user import query_command

    query_command(query, index, k=top_k)


if __name__ == "__main__":
    cli()
