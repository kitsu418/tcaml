import click

from language.lang_parser import parse
from verifier.vcgeneration import program_generate_vcs


@click.group()
def cli() -> None:
    pass


@cli.command("parse", help="show output from parsing a TCaml program")
@click.argument("file")
def parse_cli(file: str) -> None:
    try:
        with open(file, "r") as f:
            data = f.read()
    except:
        click.echo(f"file {file} not found")
        return

    parsed_contents = parse(data)
    click.echo(f"parsed output: {parsed_contents}")


@cli.command("recurrences", help="show recurrences that need to be verified")
@click.argument("file")
def recurrences_cli(file: str) -> None:
    try:
        with open(file, "r") as f:
            data = f.read()
    except:
        click.echo(f"file {file} not found")
        return

    parsed_contents = parse(data)
    vcs = program_generate_vcs(parsed_contents)  # type: ignore
    click.echo(vcs)


if __name__ == "__main__":
    cli()
