import click

from language.lang_parser import parse


@click.group()
def cli() -> None:
    pass


@cli.command("parse", help="TCaml file to parse")
@click.argument("file")
def parse_cli(file: str) -> None:
    with open(file, "r") as f:
        data = f.read()

    if data is None:
        click.echo(f"file {file} not found")
        return

    parsed_contents = parse(data)
    click.echo(f"parsed output: {parsed_contents}")


if __name__ == "__main__":
    cli()
