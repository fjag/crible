"""Command-line interface for Crible."""
import os
import sys
import click
from pathlib import Path

from crible.utils import AnthropicClient
from crible.layers.layer0 import Layer0
from crible.layers.layer1 import Layer1
from crible.layers.layer2 import Layer2
from crible.layers.layer3 import Layer3
from crible.pipeline import PipelineOrchestrator
from crible.review_interface import ReviewInterface
from crible.output import JSONRenderer, AnnotatedMarkdownRenderer
from crible.constants import Severity


def get_api_key() -> str:
    """Get Anthropic API key from environment or config.

    Returns:
        API key string

    Raises:
        click.ClickException: If API key not found
    """
    # Try environment variable first
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        # Try config file
        config_path = Path.home() / '.crible' / 'config'
        if config_path.exists():
            with open(config_path, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        raise click.ClickException(
            "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or "
            "create ~/.crible/config with ANTHROPIC_API_KEY=your-key"
        )

    return api_key


@click.group()
def cli():
    """Crible: Quality assessment tool for bioinformatics skill files."""
    pass


@cli.command()
@click.argument('skill_file', type=click.Path(exists=True))
@click.option(
    '--format',
    type=click.Choice(['annotated', 'json']),
    default='annotated',
    help='Output format (default: annotated)'
)
@click.option(
    '--output',
    type=click.Path(),
    default=None,
    help='Output file path (default: <skill_name>_crible_report.md or .json)'
)
@click.option(
    '--no-review',
    is_flag=True,
    help='Skip interactive review (accept all findings)'
)
@click.option(
    '--skip-layer',
    multiple=True,
    type=int,
    help='Skip specific layer (can be repeated)'
)
@click.option(
    '--model',
    type=click.Choice(['sonnet', 'opus', 'haiku']),
    default='sonnet',
    help='Claude model to use (default: sonnet)'
)
@click.option(
    '--verbose',
    is_flag=True,
    help='Show detailed execution logs'
)
def assess(skill_file, format, output, no_review, skip_layer, model, verbose):
    """Run quality assessment on a bioinformatics skill file.

    The report is saved to a file (default: <skill_name>_crible_report.md).
    You can specify a custom output path with --output.

    \b
    Examples:
        crible assess skill.md
        crible assess skill.md --format json
        crible assess skill.md --output custom_report.md
        crible assess skill.md --no-review --skip-layer 0
        crible assess skill.md --model opus --verbose
    """
    try:
        # Get API key
        api_key = get_api_key()

        # Initialize LLM client
        llm_client = AnthropicClient(api_key=api_key, model=model)

        # Initialize layers
        layers = [
            Layer0(llm_client),
            Layer1(llm_client),
            Layer2(llm_client),
            Layer3(llm_client),
        ]

        # Create pipeline orchestrator
        orchestrator = PipelineOrchestrator(llm_client, layers)

        # Run assessment
        if verbose:
            click.echo(f"Assessing: {skill_file}")
            click.echo(f"Model: {model}")

        report = orchestrator.run(
            skill_file_path=skill_file,
            skip_layers=list(skip_layer),
            verbose=verbose
        )

        # Interactive review (unless skipped)
        if not no_review and report.findings:
            if verbose:
                click.echo("\nStarting interactive review...")

            review_interface = ReviewInterface()
            report.findings = review_interface.run_review(report.findings)

        # Read original skill content for annotated output
        with open(skill_file, 'r', encoding='utf-8') as f:
            skill_content = f.read()

        # Render output
        if format == 'json':
            output_text = JSONRenderer.render(report, pretty=True)
        else:  # annotated
            renderer = AnnotatedMarkdownRenderer()
            output_text = renderer.render(report, skill_content)

        # Determine output file
        if not output:
            # Generate default filename based on input
            from pathlib import Path
            skill_path = Path(skill_file)
            extension = '.json' if format == 'json' else '.md'
            output = f"{skill_path.stem}_crible_report{extension}"

        # Write output
        with open(output, 'w', encoding='utf-8') as f:
            f.write(output_text)

        click.echo(f"\n{'='*60}")
        click.echo(f"✓ Assessment complete!")
        click.echo(f"{'='*60}")
        click.echo(f"Report saved to: [bold]{output}[/bold]")

        # Show quick summary
        summary = report.summary_stats()
        click.echo(f"\nFindings: {summary['total_findings']} total ")
        click.echo(f"  • Critical: {summary['by_severity'][Severity.CRITICAL]}")
        click.echo(f"  • Warnings: {summary['by_severity'][Severity.WARNING]}")
        click.echo(f"  • Info: {summary['by_severity'][Severity.INFO]}")
        click.echo(f"\nOpen the report file to view detailed findings.")

        # Exit with error code if critical findings
        if summary['by_severity'][Severity.CRITICAL] > 0:
            if verbose:
                click.echo(f"\nWarning: {summary['by_severity'][Severity.CRITICAL]} critical findings detected")
            sys.exit(1)

    except Exception as e:
        raise click.ClickException(str(e))


@cli.command()
def version():
    """Show Crible version."""
    click.echo("Crible v0.2.0")


@cli.command()
def setup():
    """Interactive setup for API key configuration."""
    click.echo("Crible Setup\n")

    api_key = click.prompt("Enter your Anthropic API key", hide_input=True)

    # Create config directory
    config_dir = Path.home() / '.crible'
    config_dir.mkdir(exist_ok=True)

    # Save API key
    config_path = config_dir / 'config'
    with open(config_path, 'w') as f:
        f.write(f"ANTHROPIC_API_KEY={api_key}\n")

    config_path.chmod(0o600)  # Secure permissions

    click.echo(f"\nAPI key saved to: {config_path}")
    click.echo("You can now run: crible assess <skill-file.md>")


if __name__ == '__main__':
    cli()
