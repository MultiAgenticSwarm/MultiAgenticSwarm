"""
Main entry point for the multiagenticswarm package.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from .core.system import System
from .utils.logger import setup_logger


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="MultiAgenticSwarm - LangGraph-based multi-agent orchestration"
    )
    
    parser.add_argument(
        "--config",
        "-c", 
        type=str,
        help="Path to configuration file (JSON or YAML)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port for web interface (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost", 
        help="Host for web interface (default: localhost)"
    )
    
    parser.add_argument(
        "--mode",
        "-m",
        choices=["cli", "web", "api"],
        default="cli",
        help="Run mode: cli, web, or api (default: cli)"
    )

    args = parser.parse_args()
    
    # Setup logging
    setup_logger(verbose=args.verbose)
    
    try:
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"Error: Configuration file '{args.config}' not found.")
                sys.exit(1)
            
            # Load system from config
            system = System.from_config(str(config_path))
        else:
            # Create empty system for interactive use
            system = System()
            print("No configuration provided. Starting with empty system.")
            print("Use System.from_config() or register components manually.")
        
        # Run based on mode
        if args.mode == "cli":
            print("Starting MultiAgenticSwarm in CLI mode...")
            asyncio.run(system.run_async())
            
        elif args.mode == "web":
            print(f"Starting web interface on http://{args.host}:{args.port}")
            from .web.app import create_app
            app = create_app(system)
            import uvicorn
            uvicorn.run(app, host=args.host, port=args.port)
            
        elif args.mode == "api":
            print(f"Starting API server on http://{args.host}:{args.port}")
            from .api.server import create_api
            api = create_api(system)
            import uvicorn
            uvicorn.run(api, host=args.host, port=args.port)
            
    except KeyboardInterrupt:
        print("\nShutting down MultiAgenticSwarm...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
