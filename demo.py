"""Command-line demo for the complete API reliability agent."""

import argparse
import asyncio
from urllib.parse import urlparse

from agents import Runner

from app.agent import complete_api_reliability_agent


def valid_target_url(value: str) -> str:
    """Accept only absolute HTTP(S) URLs and normalize trailing slashes."""

    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError(
            "target must be an absolute HTTP(S) URL"
        )

    return value.rstrip("/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run every registered read-only API reliability check."
    )
    parser.add_argument(
        "--target",
        required=True,
        type=valid_target_url,
        help="Base URL of the API to inspect",
    )
    return parser.parse_args()


async def run_demo(target_url: str) -> None:
    prompt = (
        f"Target API: {target_url}/\n"
        "Run the complete read-only reliability check."
    )
    result = await Runner.run(complete_api_reliability_agent, prompt)
    print(result.final_output)


def main() -> None:
    args = parse_args()
    asyncio.run(run_demo(args.target))


if __name__ == "__main__":
    main()