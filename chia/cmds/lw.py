import asyncio
import click

@click.group("lw", short_help="Light Wallet")
def lw_cmd():
    """Accounting functions without synching the wallet"""

@lw_cmd.command("show", short_help="Show the wallet balances for all configured keys. Good luck approach for first 500 puzzle hashes.")
@click.pass_context
def show_cmd(ctx: click.Context):
    from .lw_funcs import show
    from pathlib import Path

    root_path: Path = ctx.obj["root_path"]

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(show(root_path))
    finally:
        loop.close()

