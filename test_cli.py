import typer

app = typer.Typer()

@app.command()
def assistant():
    typer.echo("Hello from assistant!")

if __name__ == "__main__":
    app()
