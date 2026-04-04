"""Interactive review interface for assessment findings."""
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from crible.models import Finding
from crible.constants import Severity, ReviewDecision, SEVERITY_STYLE


class ReviewInterface:
    """Terminal-based interactive review interface using Rich library."""

    def __init__(self):
        self.console = Console()

    def run_review(self, findings: List[Finding]) -> List[Finding]:
        """Present findings interactively for user review.

        Args:
            findings: List of findings to review

        Returns:
            Updated findings list with review decisions
        """
        if not findings:
            self.console.print("[bold green]No findings to review!")
            return findings

        self.console.print("\n[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
        self.console.print("[bold cyan]║[/bold cyan]           [bold white]Crible Assessment Review[/bold white]                      [bold cyan]║[/bold cyan]")
        self.console.print("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]\n")

        self.console.print(f"[dim]Total findings:[/dim] [bold]{len(findings)}[/bold]")
        self.console.print("\n[bold]How to review:[/bold]")
        self.console.print("  • Type [green]a[/green] or [green]accept[/green] - Keep this finding as-is")
        self.console.print("  • Type [red]d[/red] or [red]dismiss[/red] - Mark as false positive (requires reason)")
        self.console.print("  • Type [yellow]n[/yellow] or [yellow]annotate[/yellow] - Add context note to this finding")
        self.console.print("  • Type [blue]s[/blue] or [blue]skip_all[/blue] - Accept all remaining findings")
        self.console.print()

        # Group by severity
        grouped = self._group_by_severity(findings)

        # Track review progress
        reviewed_count = 0

        for severity in Severity.ALL:
            severity_findings = grouped[severity]
            if not severity_findings:
                continue

            style = SEVERITY_STYLE[severity]
            self.console.print(f"\n[{style}]{'='*60}[/{style}]")
            self.console.print(f"[{style}]{severity.upper()} FINDINGS ({len(severity_findings)})[/{style}]")
            self.console.print(f"[{style}]{'='*60}[/{style}]\n")

            for i, finding in enumerate(severity_findings, 1):
                self._display_finding(finding, i, len(severity_findings))

                decision = self._prompt_decision()

                if decision == "dismiss":
                    reason = self._prompt_reason()
                    finding.review_decision = ReviewDecision.DISMISSED
                    finding.review_note = f"User review: {reason}"
                    self.console.print("[red]✓ Dismissed[/red]")
                    self.console.print("[dim]" + "─" * 60 + "[/dim]\n")

                elif decision == "annotate":
                    note = self._prompt_annotation()
                    finding.review_decision = ReviewDecision.ANNOTATED
                    finding.review_note = f"User review: {note}"
                    self.console.print("[yellow]✓ Annotated[/yellow]")
                    self.console.print("[dim]" + "─" * 60 + "[/dim]\n")

                elif decision == "skip_all":
                    # Accept all remaining findings
                    self.console.print("\n[yellow]⏭ Accepting all remaining findings...[/yellow]\n")
                    for remaining_finding in severity_findings[i-1:]:
                        if remaining_finding.review_decision is None:
                            remaining_finding.review_decision = ReviewDecision.ACCEPTED
                    # Move to next severity level
                    break

                else:  # accept
                    finding.review_decision = ReviewDecision.ACCEPTED
                    self.console.print("[green]✓ Accepted[/green]")
                    self.console.print("[dim]" + "─" * 60 + "[/dim]\n")

                reviewed_count += 1

        # Show summary
        self._display_summary(findings)

        return findings

    def _group_by_severity(self, findings: List[Finding]) -> dict:
        """Group findings by severity."""
        grouped = {s: [] for s in Severity.ALL}
        for finding in findings:
            if finding.severity in grouped:
                grouped[finding.severity].append(finding)
        return grouped

    def _display_finding(self, finding: Finding, index: int, total: int):
        """Display a single finding."""
        style = SEVERITY_STYLE[finding.severity]

        # Create table for structured display
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("Finding", f"{index} of {total}")
        table.add_row("Layer", f"{finding.layer_id}: {finding.layer_name}")
        table.add_row("Location", finding.location)
        table.add_row("Category", finding.category.replace('_', ' ').title())

        if finding.confidence is not None:
            table.add_row("Confidence", f"{finding.confidence:.2f}")

        panel = Panel(
            table,
            title=f"[{style}]{finding.severity.upper()}[/{style}]",
            border_style=style,
        )

        self.console.print(panel)
        self.console.print(f"\n[bold]Issue:[/bold] {finding.description}")
        self.console.print(f"[bold]Recommendation:[/bold] {finding.recommendation}\n")

    def _prompt_decision(self) -> str:
        """Prompt user for review decision."""
        self.console.print("\n[bold]Your decision:[/bold] [green][A]ccept[/green] / [red][D]ismiss[/red] / [yellow]A[N]notate[/yellow] / [blue][S]kip all[/blue]", end=" ")
        choice = Prompt.ask(
            "",
            choices=["accept", "a", "dismiss", "d", "annotate", "n", "skip_all", "s"],
            default="accept",
            show_choices=False,
        )
        # Normalize single-letter shortcuts
        shortcuts = {"a": "accept", "d": "dismiss", "n": "annotate", "s": "skip_all"}
        return shortcuts.get(choice, choice)

    def _prompt_reason(self) -> str:
        """Prompt user for dismissal reason."""
        reason = Prompt.ask("[bold]Reason for dismissal[/bold]")
        return reason

    def _prompt_annotation(self) -> str:
        """Prompt user for annotation text."""
        note = Prompt.ask("[bold]Annotation note[/bold]")
        return note

    def _display_summary(self, findings: List[Finding]):
        """Display review summary."""
        self.console.print("\n[bold]Review Summary[/bold]\n")

        accepted = sum(1 for f in findings if f.review_decision == ReviewDecision.ACCEPTED)
        dismissed = sum(1 for f in findings if f.review_decision == ReviewDecision.DISMISSED)
        annotated = sum(1 for f in findings if f.review_decision == ReviewDecision.ANNOTATED)

        summary_table = Table()
        summary_table.add_column("Decision", style="bold")
        summary_table.add_column("Count", justify="right")

        summary_table.add_row("Accepted", f"[green]{accepted}[/green]")
        summary_table.add_row("Dismissed", f"[red]{dismissed}[/red]")
        summary_table.add_row("Annotated", f"[blue]{annotated}[/blue]")
        summary_table.add_row("Total", f"[bold]{len(findings)}[/bold]")

        self.console.print(summary_table)
        self.console.print()

        # Confirm
        proceed = Confirm.ask("[bold]Proceed to generate report?[/bold]", default=True)
        if not proceed:
            self.console.print("[yellow]Review cancelled. Exiting...[/yellow]")
            exit(0)
