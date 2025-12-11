import click
import time
import json
from pathlib import Path

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


def collect_benchmark(file_path: str) -> dict:
    """Collect statistics for a single file"""
    start_time = time.time()
    
    try:
        with open(file_path, "r") as f:
            data = f.read()
    except Exception as e:
        return {
            "file": file_path,
            "error": f"Failed to read file: {str(e)}"
        }
    
    # Parse phase
    parse_start = time.time()
    try:
        parsed = parse(data)
        parse_time = time.time() - parse_start
    except Exception as e:
        return {
            "file": file_path,
            "error": f"Parse failed: {str(e)}",
            "parse_time": time.time() - parse_start
        }
    
    # VC generation phase
    vc_start = time.time()
    try:
        results = program_generate_vcs(parsed)
        vc_time = time.time() - vc_start
    except Exception as e:
        return {
            "file": file_path,
            "error": f"VC generation failed: {str(e)}",
            "parse_time": parse_time,
            "vc_generation_time": time.time() - vc_start
        }
    
    total_time = time.time() - start_time
    
    stats = {
        "file": file_path,
        "parse_time": parse_time,
        "vc_generation_time": vc_time,
        "total_time": total_time,
        "num_functions": len(results),
        "functions": []
    }
    
    for test in results:
        func_stats = {
            "name": test.name,
            "num_paths": len(test.paths),
            "total_calls": sum(len(path) for path in test.paths),
            "max_path_length": max(len(path) for path in test.paths) if test.paths else 0,
            "min_path_length": min(len(path) for path in test.paths) if test.paths else 0,
            "avg_path_length": sum(len(path) for path in test.paths) / len(test.paths) if test.paths else 0,
        }
        stats["functions"].append(func_stats)
    
    return stats


@cli.command("analyze", help="analyze a TCaml program or collect benchmarks on all examples")
@click.argument("file_or_dir", required=False)
@click.option("--all", "run_all", is_flag=True, help="Run benchmarks on all .ml files in examples/ directory")
@click.option("--output", default="benchmark_results.json", help="Output file for benchmark results (default: benchmark_results.json)")
def analyze_cli(file_or_dir: str | None, run_all: bool, output: str) -> None:
    # If --all flag is set, run benchmarks
    if run_all:
        examples_path = Path("examples")
        if not examples_path.exists():
            click.echo(f"Error: {examples_path} directory not found")
            return
        
        examples = sorted(examples_path.glob("*.ml"))
        if not examples:
            click.echo(f"No .ml files found in {examples_path}")
            return
        
        all_stats = []
        click.echo(f"Processing {len(examples)} file(s)...\n")
        
        for example_file in examples:
            click.echo(f"Processing {example_file.name}...", nl=False)
            try:
                stats = collect_benchmark(str(example_file))
                all_stats.append(stats)
                
                if "error" in stats:
                    click.echo(f" ERROR: {stats['error']}")
                else:
                    click.echo(f" ✓ ({stats['total_time']:.3f}s)")
            except Exception as e:
                click.echo(f" EXCEPTION: {e}")
                all_stats.append({
                    "file": str(example_file),
                    "error": f"Exception: {str(e)}"
                })
        
        # Print summary
        click.echo("\n" + "="*60)
        click.echo("SUMMARY")
        click.echo("="*60)
        
        total_files = len(all_stats)
        successful = len([r for r in all_stats if "error" not in r])
        failed = total_files - successful
        
        if successful > 0:
            total_time = sum(r.get("total_time", 0) for r in all_stats if "error" not in r)
            avg_time = total_time / successful
            total_parse_time = sum(r.get("parse_time", 0) for r in all_stats if "error" not in r)
            total_vc_time = sum(r.get("vc_generation_time", 0) for r in all_stats if "error" not in r)
            
            total_functions = sum(r.get("num_functions", 0) for r in all_stats if "error" not in r)
            total_paths = sum(
                sum(f.get("num_paths", 0) for f in r.get("functions", []))
                for r in all_stats if "error" not in r
            )
            total_calls = sum(
                sum(f.get("total_calls", 0) for f in r.get("functions", []))
                for r in all_stats if "error" not in r
            )
            
            click.echo(f"Files processed: {successful}/{total_files}")
            if failed > 0:
                click.echo(f"  ✓ Successful: {successful}")
                click.echo(f"  ✗ Failed: {failed}")
            
            click.echo(f"\nTiming:")
            click.echo(f"  Total time: {total_time:.3f}s")
            click.echo(f"  Average time per file: {avg_time:.3f}s")
            click.echo(f"  Parse time: {total_parse_time:.3f}s ({total_parse_time/total_time*100:.1f}%)")
            click.echo(f"  VC generation time: {total_vc_time:.3f}s ({total_vc_time/total_time*100:.1f}%)")
            
            click.echo(f"\nAnalysis Results:")
            click.echo(f"  Total functions analyzed: {total_functions}")
            click.echo(f"  Total execution paths generated: {total_paths}")
            click.echo(f"  Total function calls across all paths: {total_calls}")
            
            if total_functions > 0:
                avg_paths_per_func = total_paths / total_functions
                avg_calls_per_func = total_calls / total_functions
                click.echo(f"  Average paths per function: {avg_paths_per_func:.2f}")
                click.echo(f"  Average calls per function: {avg_calls_per_func:.2f}")
        else:
            click.echo("No files processed successfully")
        
        if failed > 0:
            click.echo(f"\nFailed files:")
            for stats in all_stats:
                if "error" in stats:
                    click.echo(f"  - {Path(stats['file']).name}: {stats['error']}")
        
        # Save detailed results
        output_path = Path(output)
        with open(output_path, "w") as f:
            json.dump(all_stats, f, indent=2)
        click.echo(f"\nDetailed results saved to {output_path.absolute()}")
        return
    
    # If a directory is provided, run benchmarks on it
    if file_or_dir and Path(file_or_dir).is_dir():
        examples = sorted(Path(file_or_dir).glob("*.ml"))
        if not examples:
            click.echo(f"No .ml files found in {file_or_dir}")
            return
        
        all_stats = []
        click.echo(f"Processing {len(examples)} file(s) from {file_or_dir}...\n")
        
        for example_file in examples:
            click.echo(f"Processing {example_file.name}...", nl=False)
            try:
                stats = collect_benchmark(str(example_file))
                all_stats.append(stats)
                
                if "error" in stats:
                    click.echo(f" ERROR: {stats['error']}")
                else:
                    click.echo(f" ✓ ({stats['total_time']:.3f}s)")
            except Exception as e:
                click.echo(f" EXCEPTION: {e}")
                all_stats.append({
                    "file": str(example_file),
                    "error": f"Exception: {str(e)}"
                })
        
        # Print summary (simplified)
        successful = len([r for r in all_stats if "error" not in r])
        total_time = sum(r.get("total_time", 0) for r in all_stats if "error" not in r)
        click.echo(f"\n✓ Processed {successful}/{len(all_stats)} files in {total_time:.3f}s")
        
        # Save results
        output_path = Path(output)
        with open(output_path, "w") as f:
            json.dump(all_stats, f, indent=2)
        click.echo(f"Results saved to {output_path.absolute()}")
        return
    
    # Default: single file analysis
    if not file_or_dir:
        click.echo("Error: Please provide a file, directory, or use --all flag")
        click.echo("Usage: python main.py analyze <file>")
        click.echo("   or: python main.py analyze --all")
        click.echo("   or: python main.py analyze <directory>")
        return
    
    try:
        with open(file_or_dir, "r") as f:
            data = f.read()
    except:
        click.echo(f"file {file_or_dir} not found")
        return

    parsed_contents = parse(data)
    results = program_generate_vcs(parsed_contents)  # type: ignore
    
    click.echo(f"\n=== Analysis Results ===\n")
    for test in results:
        click.echo(f"Function: {test.name}")
        click.echo(f"  Time Complexity Claim: {test.info.timespec}")
        click.echo(f"  Size Parameter: {test.info.size}")
        click.echo(f"  Number of Arguments: {len(test.info.args)}")
        click.echo(f"  Number of Execution Paths: {len(test.paths)}")
        
        if test.paths:
            for i, path in enumerate(test.paths):
                click.echo(f"    Path {i+1}: {len(path)} function call(s)")
                for call in path:
                    click.echo(f"      - {call.func_name}(...)")
        else:
            click.echo("    (No function calls in this path)")
        click.echo()


if __name__ == "__main__":
    cli()
