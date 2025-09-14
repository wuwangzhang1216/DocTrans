#!/usr/bin/env python3
"""
Document Translator CLI
A professional command-line interface for translating documents using OpenAI API.
Supports PDF, PPTX, DOCX, and TXT formats with parallel processing.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import configparser
from getpass import getpass

# Import the translator module
try:
    from translate_doc import DocumentTranslator
except ImportError:
    print("Error: translate_doc.py not found in the current directory.")
    sys.exit(1)

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Supported languages mapping
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'sv': 'Swedish',
    'pl': 'Polish',
    'tr': 'Turkish',
    'he': 'Hebrew',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'cs': 'Czech',
    'hu': 'Hungarian',
    'el': 'Greek',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'ro': 'Romanian',
    'uk': 'Ukrainian',
    'bg': 'Bulgarian',
    'hr': 'Croatian',
    'sr': 'Serbian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
}

class TranslatorCLI:
    """Main CLI application class for document translation."""
    
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
    
    def print_header(self):
        """Print application header."""
        if not self.quiet:
            print(f"\n{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════╗{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.CYAN}║         Document Translator CLI v1.0                      ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.CYAN}║         Powered by OpenAI API                             ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
    
    def print_success(self, message: str):
        """Print success message."""
        if not self.quiet:
            print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}", file=sys.stderr)
    
    def print_warning(self, message: str):
        """Print warning message."""
        if not self.quiet:
            print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message."""
        if not self.quiet:
            print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")
    
    def get_api_key(self, args) -> Optional[str]:
        """Get API key from args, env, config, or prompt."""
        # Priority: CLI arg > env var > config file > prompt
        api_key = None
        
        if args.api_key:
            api_key = args.api_key
            source = "command line"
        elif 'OPENAI_API_KEY' in os.environ:
            api_key = os.environ['OPENAI_API_KEY']
            source = "environment variable"
        elif self.config.has_option('api', 'key'):
            api_key = self.config.get('api', 'key')
            source = "config file"
        else:
            self.print_warning("No API key found. Please enter your OpenAI API key:")
            api_key = getpass("API Key: ")
            
            # Ask if user wants to save it
            save = input("\nSave API key for future use? (y/n): ").lower()
            if save == 'y':
                if not self.config.has_section('api'):
                    self.config.add_section('api')
                self.config.set('api', 'key', api_key)
                self.save_config()
                self.print_success("API key saved to config file")
            source = "user input"
        
        if self.verbose and api_key:
            self.print_info(f"Using API key from {source}")
        
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
        self.print_warning(f"Language '{language}' not in predefined list. Using as-is.")
        return language
    
    def translate_single(self, args):
        """Handle single file translation."""
        self.print_header()
        
        # Validate input file
        input_path = Path(args.input)
        if not input_path.exists():
            self.print_error(f"Input file not found: {input_path}")
            return 1
        
        if not input_path.is_file():
            self.print_error(f"Input path is not a file: {input_path}")
            return 1
        
        # Get API key
        api_key = self.get_api_key(args)
        if not api_key:
            self.print_error("API key is required")
            return 1
        
        # Validate language
        target_language = self.validate_language(args.language)
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            base = input_path.stem
            ext = input_path.suffix
            output_path = str(input_path.parent / f"{base}_translated_{target_language.lower()}{ext}")
        
        # Print translation info
        self.print_info(f"Input file: {input_path}")
        self.print_info(f"Output file: {output_path}")
        self.print_info(f"Target language: {target_language}")
        self.print_info(f"Model: {args.model}")
        self.print_info(f"Max workers: {args.workers}")
        
        print()  # Empty line for spacing
        
        try:
            # Initialize translator
            translator = DocumentTranslator(
                api_key=api_key,
                model=args.model,
                max_workers=args.workers
            )
            
            # Perform translation
            start_time = datetime.now()
            self.print_info(f"Starting translation at {start_time.strftime('%H:%M:%S')}...")
            
            success = translator.translate_document(
                input_path=str(input_path),
                output_path=output_path,
                target_language=target_language
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if success:
                self.print_success(f"Translation completed in {duration:.2f} seconds")
                self.print_success(f"Output saved to: {output_path}")
                
                # Show file size comparison
                input_size = input_path.stat().st_size / 1024  # KB
                output_size = Path(output_path).stat().st_size / 1024 if Path(output_path).exists() else 0
                self.print_info(f"File sizes - Input: {input_size:.2f}KB, Output: {output_size:.2f}KB")
                
                return 0
            else:
                self.print_error("Translation failed")
                return 1
                
        except Exception as e:
            self.print_error(f"Unexpected error: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def translate_batch(self, args):
        """Handle batch translation of multiple files."""
        self.print_header()
        
        # Validate input folder
        input_folder = Path(args.input_folder)
        if not input_folder.exists():
            self.print_error(f"Input folder not found: {input_folder}")
            return 1
        
        if not input_folder.is_dir():
            self.print_error(f"Input path is not a folder: {input_folder}")
            return 1
        
        # Create output folder
        output_folder = Path(args.output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Get API key
        api_key = self.get_api_key(args)
        if not api_key:
            self.print_error("API key is required")
            return 1
        
        # Validate language
        target_language = self.validate_language(args.language)
        
        # Parse file types
        if args.types:
            file_types = [f".{t.strip('.')}" for t in args.types.split(',')]
        else:
            file_types = ['.pptx', '.pdf', '.docx', '.txt']
        
        # Count files to process
        files_to_process = []
        for file_path in input_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                files_to_process.append(file_path)
        
        if not files_to_process:
            self.print_warning(f"No files found with extensions: {', '.join(file_types)}")
            return 0
        
        # Print batch info
        self.print_info(f"Input folder: {input_folder}")
        self.print_info(f"Output folder: {output_folder}")
        self.print_info(f"Target language: {target_language}")
        self.print_info(f"File types: {', '.join(file_types)}")
        self.print_info(f"Files to process: {len(files_to_process)}")
        self.print_info(f"Model: {args.model}")
        self.print_info(f"Max workers per file: {args.workers}")
        
        print()  # Empty line for spacing
        
        try:
            # Initialize translator
            translator = DocumentTranslator(
                api_key=api_key,
                model=args.model,
                max_workers=args.workers
            )
            
            # Perform batch translation
            start_time = datetime.now()
            self.print_info(f"Starting batch translation at {start_time.strftime('%H:%M:%S')}...")
            print()
            
            results = translator.batch_translate(
                input_folder=str(input_folder),
                output_folder=str(output_folder),
                target_language=target_language,
                file_types=file_types
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Print summary
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
            print(f"{Colors.BOLD}Translation Summary:{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
            
            self.print_success(f"Successfully translated: {len(results['success'])} files")
            if results['success'] and self.verbose:
                for file in results['success']:
                    print(f"  {Colors.GREEN}✓{Colors.ENDC} {file}")
            
            if results['failed']:
                self.print_error(f"Failed: {len(results['failed'])} files")
                for file in results['failed']:
                    print(f"  {Colors.FAIL}✗{Colors.ENDC} {file}")
            
            print()
            self.print_info(f"Total time: {duration:.2f} seconds")
            self.print_info(f"Average time per file: {duration/len(files_to_process):.2f} seconds")
            
            return 0 if not results['failed'] else 1
            
        except Exception as e:
            self.print_error(f"Unexpected error: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def list_languages(self, args):
        """List all supported languages."""
        self.print_header()
        print(f"{Colors.BOLD}Supported Languages:{Colors.ENDC}\n")
        
        # Create two-column layout
        languages = list(SUPPORTED_LANGUAGES.items())
        mid = len(languages) // 2
        
        for i in range(mid):
            left = languages[i]
            right = languages[i + mid] if i + mid < len(languages) else ('', '')
            
            left_str = f"{Colors.CYAN}{left[0]:4}{Colors.ENDC} - {left[1]}"
            right_str = f"{Colors.CYAN}{right[0]:4}{Colors.ENDC} - {right[1]}" if right[0] else ""
            
            print(f"  {left_str:35} {right_str}")
        
        print(f"\n{Colors.BLUE}ℹ You can use either the code (e.g., 'zh') or full name (e.g., 'Chinese'){Colors.ENDC}")
        return 0
    
    def configure(self, args):
        """Configure application settings."""
        self.print_header()
        print(f"{Colors.BOLD}Configuration Settings:{Colors.ENDC}\n")
        
        # API Key configuration
        if args.set_key:
            if not self.config.has_section('api'):
                self.config.add_section('api')
            self.config.set('api', 'key', args.set_key)
            self.save_config()
            self.print_success("API key saved to config file")
        
        # Default model configuration
        if args.set_model:
            if not self.config.has_section('defaults'):
                self.config.add_section('defaults')
            self.config.set('defaults', 'model', args.set_model)
            self.save_config()
            self.print_success(f"Default model set to: {args.set_model}")
        
        # Default workers configuration
        if args.set_workers:
            if not self.config.has_section('defaults'):
                self.config.add_section('defaults')
            self.config.set('defaults', 'workers', str(args.set_workers))
            self.save_config()
            self.print_success(f"Default workers set to: {args.set_workers}")
        
        # Show current configuration
        if args.show or (not args.set_key and not args.set_model and not args.set_workers):
            print("Current configuration:\n")
            
            if self.config.has_option('api', 'key'):
                api_key = self.config.get('api', 'key')
                masked_key = api_key[:10] + '...' + api_key[-4:] if len(api_key) > 14 else '***'
                print(f"  API Key: {Colors.CYAN}{masked_key}{Colors.ENDC}")
            else:
                print(f"  API Key: {Colors.WARNING}Not set{Colors.ENDC}")
            
            if self.config.has_option('defaults', 'model'):
                print(f"  Default Model: {Colors.CYAN}{self.config.get('defaults', 'model')}{Colors.ENDC}")
            else:
                print(f"  Default Model: {Colors.CYAN}gpt-4.1-mini{Colors.ENDC} (default)")
            
            if self.config.has_option('defaults', 'workers'):
                print(f"  Default Workers: {Colors.CYAN}{self.config.get('defaults', 'workers')}{Colors.ENDC}")
            else:
                print(f"  Default Workers: {Colors.CYAN}16{Colors.ENDC} (default)")
            
            print(f"\n  Config file: {Colors.BLUE}{self.config_file}{Colors.ENDC}")
        
        return 0
    
    def run(self):
        """Main entry point for the CLI application."""
        parser = argparse.ArgumentParser(
            prog='doctranslator',
            description='Professional document translator using OpenAI API',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s translate document.pdf -l Chinese
  %(prog)s translate presentation.pptx -l Spanish -o spanish_presentation.pptx
  %(prog)s batch ./documents ./translated -l French
  %(prog)s batch ./input ./output -l Japanese --types "docx,txt"
  %(prog)s languages
  %(prog)s config --set-key sk-...
            """
        )
        
        # Global arguments
        parser.add_argument('-v', '--verbose', action='store_true',
                          help='Enable verbose output')
        parser.add_argument('-q', '--quiet', action='store_true',
                          help='Suppress non-error output')
        parser.add_argument('--api-key', help='OpenAI API key (overrides config/env)')
        
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
        translate_parser.add_argument('-m', '--model', default='gpt-4.1-mini',
                                     help='OpenAI model to use (default: gpt-4.1-mini)')
        translate_parser.add_argument('-w', '--workers', type=int, default=16,
                                     help='Max parallel workers (default: 16)')
        
        # Batch command
        batch_parser = subparsers.add_parser('batch',
                                            help='Translate multiple documents')
        batch_parser.add_argument('input_folder', help='Input folder path')
        batch_parser.add_argument('output_folder', help='Output folder path')
        batch_parser.add_argument('-l', '--language', required=True,
                                 help='Target language (e.g., Chinese, zh)')
        batch_parser.add_argument('-t', '--types',
                                 help='File types to process (comma-separated, e.g., "pptx,docx")')
        batch_parser.add_argument('-m', '--model', default='gpt-4.1-mini',
                                 help='OpenAI model to use (default: gpt-4.1-mini)')
        batch_parser.add_argument('-w', '--workers', type=int, default=16,
                                 help='Max parallel workers per file (default: 16)')
        
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
    """Main entry point."""
    try:
        app = TranslatorCLI()
        sys.exit(app.run())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Translation cancelled by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"{Colors.FAIL}Fatal error: {str(e)}{Colors.ENDC}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()