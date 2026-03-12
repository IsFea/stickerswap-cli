from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import (
    analyze_pack,
    encode_pack,
    fetch_pack,
    publish_pack,
    summarize_manifest,
    swap_faces,
    validate_pack,
)
from .runner import RunOptions, run_check, run_guided, run_live_test


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stickerswap", description="Telegram video sticker face-swap pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    guided = subparsers.add_parser("run", help="Guided end-to-end run with prompts and local config")
    guided.add_argument("--source-pack")
    guided.add_argument("--face-image", type=Path)
    guided.add_argument("--workdir", type=Path)
    guided.add_argument("--output-pack-name")
    guided.add_argument("--output-pack-title")
    guided.add_argument("--resume", action="store_true")
    guided.add_argument("--yes", action="store_true")
    guided.add_argument("--no-auto-install", action="store_true")
    guided.add_argument("--no-save-local", action="store_true")

    check = subparsers.add_parser("check", help="Run local pre-publish checks")

    live = subparsers.add_parser("test-live", help="Run a gated live Telegram integration test with 1 sticker")
    live.add_argument("--source-pack", required=True)
    live.add_argument("--face-image", required=True, type=Path)
    live.add_argument("--yes", action="store_true")

    fetch = subparsers.add_parser("fetch-pack", help="Download source video sticker pack into workspace")
    fetch.add_argument("--source-pack", required=True)
    fetch.add_argument("--workdir", type=Path, default=Path("workspace"))
    fetch.add_argument("--resume", action="store_true")
    fetch.add_argument("--limit", type=int, default=None)

    analyze = subparsers.add_parser("analyze-pack", help="Detect candidate stickers with one dominant face")
    analyze.add_argument("--workdir", type=Path, default=Path("workspace"))
    analyze.add_argument("--limit", type=int, default=None)
    analyze.add_argument("--resume", action="store_true")

    swap = subparsers.add_parser("swap-faces", help="Run face-swap over ready stickers")
    swap.add_argument("--workdir", type=Path, default=Path("workspace"))
    swap.add_argument("--face-image", required=True, type=Path)
    swap.add_argument("--resume", action="store_true")

    encode = subparsers.add_parser("encode-pack", help="Encode swapped outputs to Telegram WEBM")
    encode.add_argument("--workdir", type=Path, default=Path("workspace"))
    encode.add_argument("--resume", action="store_true")

    validate = subparsers.add_parser("validate-pack", help="Validate encoded stickers against Telegram constraints")
    validate.add_argument("--workdir", type=Path, default=Path("workspace"))

    publish = subparsers.add_parser("publish-pack", help="Publish validated stickers through Telegram Bot API")
    publish.add_argument("--workdir", type=Path, default=Path("workspace"))
    publish.add_argument("--resume", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    project_root = Path.cwd()
    if args.command == "run":
        run_guided(
            project_root,
            RunOptions(
                source_pack=args.source_pack,
                face_image=args.face_image,
                workdir=args.workdir,
                output_pack_name=args.output_pack_name,
                output_pack_title=args.output_pack_title,
                resume=args.resume,
                assume_yes=args.yes,
                auto_install=not args.no_auto_install,
                save_local=not args.no_save_local,
            ),
        )
        return
    if args.command == "check":
        run_check(project_root)
        return
    if args.command == "test-live":
        run_live_test(project_root, args.source_pack, args.face_image, assume_yes=args.yes)
        return
    if args.command == "fetch-pack":
        manifest = fetch_pack(args.workdir, args.source_pack, resume=args.resume, limit=args.limit)
    elif args.command == "analyze-pack":
        manifest = analyze_pack(args.workdir, limit=args.limit, resume=args.resume)
    elif args.command == "swap-faces":
        manifest = swap_faces(args.workdir, args.face_image, resume=args.resume)
    elif args.command == "encode-pack":
        manifest = encode_pack(args.workdir, resume=args.resume)
    elif args.command == "validate-pack":
        manifest = validate_pack(args.workdir)
    elif args.command == "publish-pack":
        manifest = publish_pack(args.workdir, resume=args.resume)
    else:  # pragma: no cover
        parser.error(f"Unknown command: {args.command}")
        return
    print(summarize_manifest(manifest))


if __name__ == "__main__":  # pragma: no cover
    main()
