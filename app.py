#!/usr/bin/env python3
"""
DocTrans CLI - Professional Document Translator
A beautiful command-line interface for translating documents using OpenRouter API.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import configparser
from getpass import getpass

# Rich imports for beautiful CLI
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.align import Align
from rich.columns import Columns
from rich.live import Live
from rich.spinner import Spinner
from rich import box
from rich.rule import Rule

# Import the translator module
try:
    from translators import DocumentTranslator
except ImportError:
    console = Console()
    console.print("[red]✗ Error:[/red] translators module not found.")
    console.print("[yellow]Please ensure the translators package is installed.[/yellow]")
    sys.exit(1)

# Initialize Rich console
console = Console()

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
    'nl': 'Dutch', 'sv': 'Swedish', 'pl': 'Polish', 'tr': 'Turkish',
    'he': 'Hebrew', 'no': 'Norwegian', 'da': 'Danish', 'fi': 'Finnish',
    'cs': 'Czech', 'hu': 'Hungarian', 'el': 'Greek', 'th': 'Thai',
    'vi': 'Vietnamese', 'id': 'Indonesian', 'ms': 'Malay', 'ro': 'Romanian',
    'uk': 'Ukrainian', 'bg': 'Bulgarian', 'hr': 'Croatian', 'sr': 'Serbian',
    'sk': 'Slovak', 'sl': 'Slovenian', 'et': 'Estonian', 'lv': 'Latvian',
    'lt': 'Lithuanian',
}

class ModernTranslatorCLI:
    """Modern CLI application with Rich interface for document translation."""

    def __init__(self):
        self.config_file = Path.home() / '.doctranslator' / 'config.ini'
        self.config = self.load_config()
        self.verbose = False
        self.quiet = False

    def load_config(self) -> configparser.ConfigParser:
        """Load configuration from file if it exists."""
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file)
        return config

    def save_config(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def print_banner(self):
        """Print beautiful application banner."""
        if self.quiet:
            return

        banner_text = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██████╗  ██████╗  ██████╗████████╗██████╗  █████╗ ███╗   ██╗ ║
║     ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗████╗  ██║ ║
║     ██║  ██║██║   ██║██║        ██║   ██████╔╝███████║██╔██╗ ██║ ║
║     ██║  ██║██║   ██║██║        ██║   ██╔══██╗██╔══██║██║╚██╗██║ ║
║     ██████╔╝╚██████╔╝╚██████╗   ██║   ██║  ██║██║  ██║██║ ╚████║ ║
║     ╚═════╝  ╚═════╝  ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ║
║                                                                  ║
║               Professional Document Translator v2.0              ║
║                    Powered by Google Gemini AI                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """

        console.print(Panel(
            Align.center(Text(banner_text, style="cyan bold")),
            border_style="bright_blue",
            padding=(0, 0)
        ))
        console.print()

    def get_api_key(self, args) -> Optional[str]:
        """Get API key from args, env, config, or prompt with beautiful UI."""
        api_key = None
        source = None

        if args.api_key:
            api_key = args.api_key
            source = "command line"
        elif 'GEMINI_API_KEY' in os.environ:
            api_key = os.environ['GEMINI_API_KEY']
            source = "environment variable (GEMINI_API_KEY)"
        elif 'OPENAI_API_KEY' in os.environ:
            # Backward compatibility
            api_key = os.environ['OPENAI_API_KEY']
            source = "environment variable (OPENAI_API_KEY)"
        elif self.config.has_option('api', 'key'):
            api_key = self.config.get('api', 'key')
            source = "config file"
        else:
            console.print(Panel(
                "[yellow]No API key found. Please enter your Gemini API key:[/yellow]\n"
                "[dim]Get your key from: https://ai.google.dev/[/dim]",
                title="[bold]API Configuration[/bold]",
                border_style="yellow"
            ))

            api_key = Prompt.ask("[cyan]Gemini API Key[/cyan]", password=True)

            # Ask if user wants to save it
            if Confirm.ask("\n[cyan]Save API key for future use?[/cyan]"):
                if not self.config.has_section('api'):
                    self.config.add_section('api')
                self.config.set('api', 'key', api_key)
                self.save_config()
                console.print("[green]✓[/green] API key saved to config file")
            source = "user input"

        if self.verbose and api_key:
            console.print(f"[dim]Using API key from {source}[/dim]")

        return api_key

    def validate_language(self, language: str) -> str:
        """Validate and normalize language input."""
        # Check if it's a language code
        if language.lower() in SUPPORTED_LANGUAGES:
            return SUPPORTED_LANGUAGES[language.lower()]

        # Check if it's a full language name
        for code, name in SUPPORTED_LANGUAGES.items():
            if name.lower() == language.lower():
                return name

        # If not found, return as-is and let the API handle it
        console.print(f"[yellow]⚠ Language '{language}' not in predefined list. Using as-is.[/yellow]")
        return language

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def translate_single(self, args):
        """Handle single file translation with beautiful progress display."""
        self.print_banner()

        # Validate input file
        input_path = Path(args.input)
        if not input_path.exists():
            console.print(f"[red]✗ Input file not found:[/red] {input_path}")
            return 1

        if not input_path.is_file():
            console.print(f"[red]✗ Input path is not a file:[/red] {input_path}")
            return 1

        # Get API key
        api_key = self.get_api_key(args)
        if not api_key:
            console.print("[red]✗ API key is required[/red]")
            return 1

        # Validate language
        target_language = self.validate_language(args.language)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            base = input_path.stem
            ext = input_path.suffix
            lang_code = args.language[:2].lower()
            output_path = str(input_path.parent / f"{base}_{lang_code}{ext}")

        # Display translation info in a beautiful table
        info_table = Table(title="Translation Details", box=box.ROUNDED, show_header=False)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")

        input_size = self.format_file_size(input_path.stat().st_size)
        info_table.add_row("📄 Input File", str(input_path))
        info_table.add_row("📁 Output File", str(output_path))
        info_table.add_row("🌍 Target Language", target_language)
        info_table.add_row("🤖 Model", args.model)
        info_table.add_row("⚡ Max Workers", str(args.workers))
        info_table.add_row("📊 File Size", input_size)

        console.print(info_table)
        console.print()

        try:
            # Initialize translator
            translator = DocumentTranslator(
                api_key=api_key,
                model=args.model,
                max_workers=args.workers
            )

            # Perform translation with progress indicator
            start_time = datetime.now()

            with console.status("[bold cyan]Initializing translation...[/bold cyan]", spinner="dots") as status:
                time.sleep(0.5)  # Small delay for visual effect
                status.update("[bold cyan]Analyzing document structure...[/bold cyan]")
                time.sleep(0.5)
                status.update("[bold cyan]Extracting content...[/bold cyan]")
                time.sleep(0.5)

            # Create progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console,
                expand=True
            ) as progress:

                task = progress.add_task(
                    f"[cyan]Translating to {target_language}...[/cyan]",
                    total=100
                )

                # Simulate progress updates (in real implementation, you'd update based on actual progress)
                progress.update(task, advance=20, description="[cyan]Processing document...[/cyan]")

                # Determine PDF method if applicable
                method = "auto"  # default
                if input_path.suffix.lower() == '.pdf' and hasattr(args, 'pdf_method'):
                    method = args.pdf_method

                # Perform actual translation
                success = translator.translate_document(
                    input_path=str(input_path),
                    output_path=output_path,
                    target_language=target_language,
                    method=method
                )

                progress.update(task, completed=100)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if success:
                # Success panel
                output_size = self.format_file_size(Path(output_path).stat().st_size)

                success_panel = Panel(
                    f"""[green]✓ Translation completed successfully![/green]

⏱  Duration: [cyan]{duration:.2f} seconds[/cyan]
📄 Output saved to: [cyan]{output_path}[/cyan]
📊 File sizes: Input [dim]{input_size}[/dim] → Output [dim]{output_size}[/dim]""",
                    title="[bold green]Success[/bold green]",
                    border_style="green",
                    box=box.DOUBLE
                )
                console.print(success_panel)
                return 0
            else:
                console.print("[red]✗ Translation failed[/red]")
                return 1

        except Exception as e:
            error_panel = Panel(
                f"[red]Unexpected error:[/red] {str(e)}",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.DOUBLE
            )
            console.print(error_panel)
            if self.verbose:
                import traceback
                console.print_exception()
            return 1

    def translate_batch(self, args):
        """Handle batch translation with beautiful progress tracking."""
        self.print_banner()

        # Validate input folder
        input_folder = Path(args.input_folder)
        if not input_folder.exists():
            console.print(f"[red]✗ Input folder not found:[/red] {input_folder}")
            return 1

        if not input_folder.is_dir():
            console.print(f"[red]✗ Input path is not a folder:[/red] {input_folder}")
            return 1

        # Create output folder
        output_folder = Path(args.output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        # Get API key
        api_key = self.get_api_key(args)
        if not api_key:
            console.print("[red]✗ API key is required[/red]")
            return 1

        # Validate language
        target_language = self.validate_language(args.language)

        # Parse file types
        if args.types:
            file_types = [f".{t.strip('.')}" for t in args.types.split(',')]
        else:
            file_types = ['.pptx', '.pdf', '.docx', '.txt', '.md', '.markdown']

        # Count files to process
        files_to_process = []
        for file_path in input_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                files_to_process.append(file_path)

        if not files_to_process:
            console.print(f"[yellow]⚠ No files found with extensions: {', '.join(file_types)}[/yellow]")
            return 0

        # Display batch info
        batch_table = Table(title="Batch Translation Details", box=box.ROUNDED)
        batch_table.add_column("Property", style="cyan")
        batch_table.add_column("Value", style="white")

        batch_table.add_row("📁 Input Folder", str(input_folder))
        batch_table.add_row("📂 Output Folder", str(output_folder))
        batch_table.add_row("🌍 Target Language", target_language)
        batch_table.add_row("📄 File Types", ', '.join(file_types))
        batch_table.add_row("📊 Files to Process", str(len(files_to_process)))
        batch_table.add_row("🤖 Model", args.model)
        batch_table.add_row("⚡ Max Workers", str(args.workers))

        console.print(batch_table)
        console.print()

        try:
            # Initialize translator
            translator = DocumentTranslator(
                api_key=api_key,
                model=args.model,
                max_workers=args.workers
            )

            # Perform batch translation with progress bar
            start_time = datetime.now()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeRemainingColumn(),
                console=console,
                expand=True
            ) as progress:

                overall_task = progress.add_task(
                    "[cyan]Processing batch...[/cyan]",
                    total=len(files_to_process)
                )

                success_files = []
                failed_files = []

                for idx, file_path in enumerate(files_to_process, 1):
                    file_task = progress.add_task(
                        f"[dim]Translating {file_path.name}...[/dim]",
                        total=100
                    )

                    try:
                        # Simulate file processing
                        progress.update(file_task, advance=50)

                        # Here you would call the actual translation
                        # For now, we'll use the batch_translate method
                        if idx == 1:  # Only call once for actual batch processing
                            results = translator.batch_translate(
                                input_folder=str(input_folder),
                                output_folder=str(output_folder),
                                target_language=target_language,
                                file_types=file_types
                            )
                            success_files = results.get('success', [])
                            failed_files = results.get('failed', [])

                        progress.update(file_task, completed=100)
                    except Exception as e:
                        failed_files.append(str(file_path))
                        progress.update(file_task, description=f"[red]Failed: {file_path.name}[/red]")

                    progress.update(overall_task, advance=1)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Display results in a beautiful summary
            console.print()
            console.rule("[bold cyan]Translation Summary[/bold cyan]")
            console.print()

            # Create summary table
            summary_table = Table(box=box.SIMPLE_HEAD, show_header=True)
            summary_table.add_column("Status", justify="center", style="bold")
            summary_table.add_column("Count", justify="center")
            summary_table.add_column("Details", justify="left")

            if success_files:
                success_list = "\n".join([f"  ✓ {f}" for f in success_files[:5]])
                if len(success_files) > 5:
                    success_list += f"\n  ... and {len(success_files) - 5} more"
                summary_table.add_row(
                    "[green]Success[/green]",
                    f"[green]{len(success_files)}[/green]",
                    success_list if self.verbose else f"[dim]{len(success_files)} files[/dim]"
                )

            if failed_files:
                failed_list = "\n".join([f"  ✗ {f}" for f in failed_files[:5]])
                if len(failed_files) > 5:
                    failed_list += f"\n  ... and {len(failed_files) - 5} more"
                summary_table.add_row(
                    "[red]Failed[/red]",
                    f"[red]{len(failed_files)}[/red]",
                    failed_list
                )

            console.print(summary_table)
            console.print()

            # Performance metrics
            metrics_panel = Panel(
                f"""⏱  Total time: [cyan]{duration:.2f} seconds[/cyan]
📊 Average time per file: [cyan]{duration/len(files_to_process):.2f} seconds[/cyan]
✅ Success rate: [{'green' if len(failed_files) == 0 else 'yellow'}]{(len(success_files)/len(files_to_process)*100):.1f}%[/{'green' if len(failed_files) == 0 else 'yellow'}]""",
                title="[bold]Performance Metrics[/bold]",
                border_style="blue"
            )
            console.print(metrics_panel)

            return 0 if not failed_files else 1

        except Exception as e:
            console.print(f"[red]✗ Unexpected error: {str(e)}[/red]")
            if self.verbose:
                console.print_exception()
            return 1

    def list_languages(self, args):
        """List all supported languages in a beautiful table."""
        self.print_banner()

        # Create language table
        lang_table = Table(
            title="🌍 Supported Languages",
            box=box.DOUBLE_EDGE,
            show_header=True,
            header_style="bold cyan"
        )

        lang_table.add_column("Code", justify="center", style="cyan", width=8)
        lang_table.add_column("Language", justify="left", style="white", width=15)
        lang_table.add_column("Code", justify="center", style="cyan", width=8)
        lang_table.add_column("Language", justify="left", style="white", width=15)

        languages = list(SUPPORTED_LANGUAGES.items())
        mid = len(languages) // 2 + len(languages) % 2

        for i in range(mid):
            left = languages[i]
            if i + mid < len(languages):
                right = languages[i + mid]
                lang_table.add_row(left[0], left[1], right[0], right[1])
            else:
                lang_table.add_row(left[0], left[1], "", "")

        console.print(lang_table)
        console.print()
        console.print(Panel(
            "[cyan]You can use either the code (e.g., 'zh') or full name (e.g., 'Chinese')[/cyan]",
            border_style="dim"
        ))

        return 0

    def configure(self, args):
        """Configure application settings with beautiful UI."""
        self.print_banner()

        # API Key configuration
        if args.set_key:
            if not self.config.has_section('api'):
                self.config.add_section('api')
            self.config.set('api', 'key', args.set_key)
            self.save_config()
            console.print("[green]✓[/green] API key saved to config file")

        # Default model configuration
        if args.set_model:
            if not self.config.has_section('defaults'):
                self.config.add_section('defaults')
            self.config.set('defaults', 'model', args.set_model)
            self.save_config()
            console.print(f"[green]✓[/green] Default model set to: [cyan]{args.set_model}[/cyan]")

        # Default workers configuration
        if args.set_workers:
            if not self.config.has_section('defaults'):
                self.config.add_section('defaults')
            self.config.set('defaults', 'workers', str(args.set_workers))
            self.save_config()
            console.print(f"[green]✓[/green] Default workers set to: [cyan]{args.set_workers}[/cyan]")

        # Show current configuration
        if args.show or (not args.set_key and not args.set_model and not args.set_workers):
            config_table = Table(
                title="⚙️  Current Configuration",
                box=box.ROUNDED,
                show_header=False
            )
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value", style="white")

            # API Key
            if self.config.has_option('api', 'key'):
                api_key = self.config.get('api', 'key')
                masked_key = api_key[:10] + '•••' + api_key[-4:] if len(api_key) > 14 else '•••'
                config_table.add_row("🔑 API Key", f"[green]{masked_key}[/green]")
            else:
                config_table.add_row("🔑 API Key", "[yellow]Not set[/yellow]")

            # Model
            if self.config.has_option('defaults', 'model'):
                config_table.add_row("🤖 Default Model", self.config.get('defaults', 'model'))
            else:
                config_table.add_row("🤖 Default Model", "google/gemini-2.0-flash-lite [dim](default)[/dim]")

            # Workers
            if self.config.has_option('defaults', 'workers'):
                config_table.add_row("⚡ Default Workers", self.config.get('defaults', 'workers'))
            else:
                config_table.add_row("⚡ Default Workers", "256 [dim](default)[/dim]")

            config_table.add_row("📁 Config File", f"[dim]{self.config_file}[/dim]")

            console.print(config_table)

        return 0

    def run(self):
        """Main entry point for the CLI application."""
        parser = argparse.ArgumentParser(
            prog='doctrans',
            description='Professional document translator using Google Gemini AI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s translate document.pdf -l Chinese
  %(prog)s translate presentation.pptx -l Spanish -o spanish_presentation.pptx
  %(prog)s batch ./documents ./translated -l French
  %(prog)s languages
  %(prog)s config --set-key sk-...
            """
        )

        # Global arguments
        parser.add_argument('-v', '--verbose', action='store_true',
                          help='Enable verbose output')
        parser.add_argument('-q', '--quiet', action='store_true',
                          help='Suppress non-error output')
        parser.add_argument('--api-key', help='Gemini API key (overrides config/env)')

        # Subcommands
        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Translate command
        translate_parser = subparsers.add_parser('translate',
                                                help='Translate a single document')
        translate_parser.add_argument('input', help='Input file path')
        translate_parser.add_argument('-l', '--language', required=True,
                                     help='Target language (e.g., Chinese, zh)')
        translate_parser.add_argument('-o', '--output',
                                     help='Output file path (optional)')
        translate_parser.add_argument('-m', '--model', default='gemini-2.0-flash-lite',
                                     help='Model to use (default: gemini-2.0-flash-lite)')
        translate_parser.add_argument('-w', '--workers', type=int, default=256,
                                     help='Max parallel workers (default: 256)')
        translate_parser.add_argument('--pdf-method', choices=['auto', 'overlay', 'redaction'],
                                     default='auto',
                                     help='PDF translation method (default: auto)')

        # Batch command
        batch_parser = subparsers.add_parser('batch',
                                            help='Translate multiple documents')
        batch_parser.add_argument('input_folder', help='Input folder path')
        batch_parser.add_argument('output_folder', help='Output folder path')
        batch_parser.add_argument('-l', '--language', required=True,
                                 help='Target language (e.g., Chinese, zh)')
        batch_parser.add_argument('-t', '--types',
                                 help='File types to process (comma-separated, e.g., "pptx,docx")')
        batch_parser.add_argument('-m', '--model', default='gemini-2.0-flash-lite',
                                 help='Model to use (default: gemini-2.0-flash-lite)')
        batch_parser.add_argument('-w', '--workers', type=int, default=256,
                                 help='Max parallel workers per file (default: 256)')

        # Languages command
        languages_parser = subparsers.add_parser('languages',
                                                help='List supported languages')

        # Config command
        config_parser = subparsers.add_parser('config',
                                             help='Configure application settings')
        config_parser.add_argument('--set-key', help='Set API key')
        config_parser.add_argument('--set-model', help='Set default model')
        config_parser.add_argument('--set-workers', type=int, help='Set default workers')
        config_parser.add_argument('--show', action='store_true',
                                  help='Show current configuration')

        # Parse arguments
        args = parser.parse_args()

        # Set verbosity
        self.verbose = args.verbose if hasattr(args, 'verbose') else False
        self.quiet = args.quiet if hasattr(args, 'quiet') else False

        # Handle commands
        if not args.command:
            self.print_banner()
            parser.print_help()
            return 0

        if args.command == 'translate':
            return self.translate_single(args)
        elif args.command == 'batch':
            return self.translate_batch(args)
        elif args.command == 'languages':
            return self.list_languages(args)
        elif args.command == 'config':
            return self.configure(args)
        else:
            parser.print_help()
            return 0


def main():
    """Main entry point with exception handling."""
    try:
        app = ModernTranslatorCLI()
        sys.exit(app.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Translation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]✗ Fatal error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()