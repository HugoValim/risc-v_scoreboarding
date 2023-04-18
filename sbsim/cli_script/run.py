import argparse

from ..scoreboarding import ScoreboardingSIM

def parse_args() -> None:
    parser = argparse.ArgumentParser(
        description="Live view for Bluesky Queue Server scans"
    )
    parser.add_argument(
        "file-path",
        metavar="file path",
        nargs="*",
        type=str,
        help="file path for each file",
    )
    parser.add_argument(
    "-p",
    "--print-all",
    action="store_true",
    help="print all of the stages",
    )

    args = parser.parse_args()
    dict_args = vars(args)
    return dict_args


def main() -> None:
    cmd_args = parse_args()
    files = cmd_args["file-path"]
    print_all = cmd_args["print_all"]
    obj = ScoreboardingSIM(files, print_all)
    obj.execute()


if __name__ == "__main__":
    main()

