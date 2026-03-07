"""
FDA RAG System - Main CLI Interface
"""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

from .config import FDA_DOCS_PATH, VECTOR_STORE_PATH
from .document_loader import load_all_documents, discover_documents
from .chunker import create_chunker
from .vector_store import create_vector_store
from .search import create_search_engine
from .rag_chain import create_rag_chain

console = Console()


@click.group()
def cli():
    """FDA 510(k) RAG System for S-Patch CardioAI (K254255)"""
    pass


@cli.command()
@click.option('--docs-path', default=str(FDA_DOCS_PATH), help='Path to FDA documents')
@click.option('--force', is_flag=True, help='Force reindex even if store exists')
def index(docs_path: str, force: bool):
    """Index all FDA documents into the vector store"""

    docs_path = Path(docs_path)
    console.print(f"\n[bold blue]FDA Document Indexer[/bold blue]")
    console.print(f"Documents path: {docs_path}")

    # Check if vector store exists
    if (VECTOR_STORE_PATH / "chroma.sqlite3").exists() and not force:
        console.print("[yellow]Vector store already exists. Use --force to reindex.[/yellow]")

        # Show stats
        store = create_vector_store()
        stats = store.get_collection_stats()
        console.print(f"Current documents: {stats['total_documents']}")
        return

    # Discover documents
    console.print("\n[cyan]Discovering documents...[/cyan]")
    file_paths = discover_documents(docs_path)
    console.print(f"Found {len(file_paths)} documents")

    # Load documents
    console.print("\n[cyan]Loading documents...[/cyan]")
    documents = load_all_documents(docs_path)
    console.print(f"Loaded {len(documents)} document chunks")

    # Chunk documents
    console.print("\n[cyan]Chunking documents...[/cyan]")
    chunker = create_chunker()
    chunks = chunker.chunk_documents(documents)
    console.print(f"Created {len(chunks)} chunks")

    # Create vector store and add documents
    console.print("\n[cyan]Creating vector store and adding documents...[/cyan]")

    if force and (VECTOR_STORE_PATH / "chroma.sqlite3").exists():
        import shutil
        shutil.rmtree(VECTOR_STORE_PATH)
        console.print("[yellow]Deleted existing vector store[/yellow]")

    store = create_vector_store()
    added = store.add_documents(chunks)

    console.print(f"\n[bold green]Indexing complete![/bold green]")
    console.print(f"Total documents indexed: {added}")


@cli.command()
@click.argument('query')
@click.option('--k', default=10, help='Number of results')
@click.option('--category', default=None, help='Filter by category')
@click.option('--final-only', is_flag=True, help='Search only FINAL documents')
def search(query: str, k: int, category: str, final_only: bool):
    """Search FDA documents"""

    console.print(f"\n[bold blue]Searching: {query}[/bold blue]")

    # Initialize components
    store = create_vector_store()
    search_engine = create_search_engine(store)

    # Search
    results = search_engine.search(
        query,
        k=k,
        category_filter=category,
        final_only=final_only
    )

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    # Display results
    for i, result in enumerate(results, 1):
        console.print(Panel(
            f"[bold]{result.source}[/bold]\n"
            f"Category: {result.category} | Score: {result.relevance_score:.3f}\n\n"
            f"{result.content[:500]}...",
            title=f"Result {i}"
        ))


@cli.command()
@click.argument('query')
@click.option('--k', default=10, help='Number of documents to retrieve')
@click.option('--category', default=None, help='Filter by category')
def ask(query: str, k: int, category: str):
    """Ask a question about FDA documents (uses Claude for response)"""

    console.print(f"\n[bold blue]Analyzing: {query}[/bold blue]\n")

    # Initialize components
    store = create_vector_store()
    search_engine = create_search_engine(store)
    rag_chain = create_rag_chain(search_engine)

    # Query
    with console.status("[bold green]Analyzing documents..."):
        response = rag_chain.query(query, k=k, category_filter=category)

    # Display response
    console.print(Markdown(response))


@cli.command()
@click.argument('deficiency_id')
def analyze(deficiency_id: str):
    """Analyze a specific FDA deficiency (e.g., SC-11, PT-17)"""

    console.print(f"\n[bold blue]Analyzing FDA Deficiency: {deficiency_id}[/bold blue]\n")

    # Initialize components
    store = create_vector_store()
    search_engine = create_search_engine(store)
    rag_chain = create_rag_chain(search_engine)

    # Analyze
    with console.status("[bold green]Analyzing deficiency..."):
        response = rag_chain.analyze_deficiency(deficiency_id)

    # Display response
    console.print(Markdown(response))


@cli.command()
@click.argument('topic')
@click.option('--keywords', '-k', multiple=True, help='Keywords to search')
def consistency(topic: str, keywords: tuple):
    """Check document consistency for a topic (e.g., cloud service)"""

    if not keywords:
        # Default keywords for common topics
        default_keywords = {
            "cloud": ["cloud", "AWS", "web server", "nginx", "container", "deployment"],
            "interface": ["electronic interface", "interoperability", "https", "API"],
            "security": ["cybersecurity", "penetration", "vulnerability", "CVE"],
        }
        keywords = default_keywords.get(topic.lower(), [topic])

    console.print(f"\n[bold blue]Checking consistency: {topic}[/bold blue]")
    console.print(f"Keywords: {', '.join(keywords)}\n")

    # Initialize components
    store = create_vector_store()
    search_engine = create_search_engine(store)
    rag_chain = create_rag_chain(search_engine)

    # Check consistency
    with console.status("[bold green]Analyzing document consistency..."):
        response = rag_chain.check_consistency(topic, list(keywords))

    # Display response
    console.print(Markdown(response))


@cli.command()
def stats():
    """Show vector store statistics"""

    store = create_vector_store()
    stats = store.get_collection_stats()

    table = Table(title="Vector Store Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    for key, value in stats.items():
        table.add_row(key, str(value))

    console.print(table)


@cli.command()
def cloud():
    """Quick check for cloud-related references across all documents"""

    console.print("\n[bold blue]Searching for Cloud/Web Service References[/bold blue]\n")

    # Initialize components
    store = create_vector_store()
    search_engine = create_search_engine(store)

    # Search cloud references
    results = search_engine.search_cloud_references()

    # Display summary
    table = Table(title="Cloud References by Keyword")
    table.add_column("Keyword", style="cyan")
    table.add_column("Documents Found", style="green")
    table.add_column("Sample Sources", style="yellow")

    for keyword, docs in results.items():
        if docs:
            sources = ", ".join(set(d.source.split("/")[-1][:30] for d in docs[:3]))
            table.add_row(keyword, str(len(docs)), sources)
        else:
            table.add_row(keyword, "0", "-")

    console.print(table)


@cli.command()
def interactive():
    """Start interactive Q&A session"""

    console.print(Panel(
        "[bold blue]FDA RAG Interactive Session[/bold blue]\n\n"
        "Commands:\n"
        "  Type your question to search and analyze\n"
        "  'search: <query>' - Search only (no analysis)\n"
        "  'analyze: <deficiency_id>' - Analyze specific deficiency\n"
        "  'consistency: <topic>' - Check document consistency\n"
        "  'quit' or 'exit' - Exit session\n",
        title="Welcome"
    ))

    # Initialize components
    store = create_vector_store()
    search_engine = create_search_engine(store)
    rag_chain = create_rag_chain(search_engine)

    while True:
        try:
            query = console.input("\n[bold green]>>> [/bold green]").strip()

            if not query:
                continue

            if query.lower() in ('quit', 'exit', 'q'):
                console.print("[yellow]Goodbye![/yellow]")
                break

            if query.lower().startswith('search:'):
                search_query = query[7:].strip()
                results = search_engine.search(search_query)
                formatted = search_engine.format_results(results)
                console.print(Markdown(formatted))

            elif query.lower().startswith('analyze:'):
                deficiency_id = query[8:].strip()
                with console.status("[bold green]Analyzing..."):
                    response = rag_chain.analyze_deficiency(deficiency_id)
                console.print(Markdown(response))

            elif query.lower().startswith('consistency:'):
                topic = query[12:].strip()
                keywords = ["cloud", "AWS", "web server", "nginx", "deployment", "interface"]
                with console.status("[bold green]Checking consistency..."):
                    response = rag_chain.check_consistency(topic, keywords)
                console.print(Markdown(response))

            else:
                with console.status("[bold green]Analyzing..."):
                    response = rag_chain.query(query)
                console.print(Markdown(response))

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'quit' to exit[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    cli()


if __name__ == "__main__":
    main()
