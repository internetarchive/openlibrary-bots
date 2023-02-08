"""
Fix promise items
"""
import argparse
import errno
import sys

from configparser import ConfigParser
from pathlib import Path

from olclient.openlibrary import OpenLibrary, Config

DEFAULT_BATCH_SIZE = 1000
DEFAULT_START_LINE = 1
IN_FILE = "./input/in.txt"
STATE_FILE = "./input/curline.txt"
ERR_FILE = "./out/err.txt"


class FixPromiseItems:
    def __init__(
        self,
        in_file,
        state_file,
        error_file,
        ol=None,
        batch_size=DEFAULT_BATCH_SIZE,
        start_line=DEFAULT_START_LINE,
        dry_run=True,
    ):
        self.ol = ol

        self.modified = 0
        self.errors = 0
        self.matched = 0

        self.in_file = in_file
        self.error_file = error_file
        self.state_file = state_file

        self.batch_size = batch_size
        self.start_line = start_line
        self.dry_run = dry_run

    def run(self):
        with open(self.in_file, "r") as f:
            if self.start_line:
                for _ in range(1, self.start_line):
                    f.readline()
            for _ in range(self.batch_size):
                line = f.readline()
                if not line:
                    break
                edition_olid = self.extract_olid(line[:-1])  # Trim trailing newline

                try:
                    edition = self.ol.get(edition_olid)
                    modified_fields = self.update_edition(edition)
                    if not self.dry_run:
                        edition.save(f"Modified {', '.join(modified_fields)}")
                    self.modified += 1
                except Exception:
                    self.write_error(self.error_file, line[:-1])
                    self.errors += 1
                    pass

        num_processed = self.modified + self.errors + self.matched
        if not self.dry_run:
            self.write_state(self.state_file, self.start_line + num_processed)

        return {
          'processed': num_processed,
          'modified': self.modified,
          'matched': self.matched,
          'errors': self.errors,
        }

    def extract_olid(self, line):
        fields = line.split("\t")
        return fields[1].split("/")[-1]

    def update_edition(self, edition):
        modified_fields = []

        id_count = len(edition.local_id)

        local_id = next(
            (b for b in edition.local_id if b.startswith("urn:bwbsku:")), ""
        )

        # Fix local IDs:
        updated_ids = [local_id] + [
            _id for _id in edition.local_id if not _id.startswith("urn:bwbsku:")
        ]

        # Check if record was previously modified:
        if id_count == len(updated_ids):
            self.matched += 1
            return

        edition.local_id = updated_ids

        modified_fields.append("local IDs")

        # Fix identifiers:
        amazon_ids = edition.identifiers.pop("amazon", None)
        bwb_ids = edition.identifiers.pop("better_world_books", None)

        if amazon_ids:
            modified_fields.append("amazon IDs")
        if bwb_ids:
            modified_fields.append("bwb IDs")

        # Fix source_records entry:
        sku = local_id.split(":")[-1]
        source_record = next(
            (r for r in edition.source_records if r.startswith("promise:")), ""
        )
        edition.source_records = [f"{source_record}:{sku}"] + [
            r for r in edition.source_records if not r.startswith("promise:")
        ]

        modified_fields.append("source records")

        return modified_fields

    def write_error(self, path, olid):
        err_path = Path(path)
        err_path.parent.mkdir(exist_ok=True, parents=True)

        with err_path.open(mode="a") as f:
            f.write(f"{olid}\n")

    def write_state(self, path, curline):
        state_path = Path(path)
        state_path.parent.mkdir(exist_ok=True, parents=True)

        with state_path.open(mode="w") as f:
            f.write(f"{curline}")


def _parse_args():
    def config_file_subparser(subparsers):
        parser = subparsers.add_parser(
            "config", help="Configure bot via configuration file"
        )
        parser.add_argument(
            "config", metavar="config_path", help="Path to the bot configuration file"
        )
        parser.set_defaults(func=configure_and_start)

    def command_line_subparser(subparsers):
        # TODO: Make it possible to set start-line from state-file contents
        parser = subparsers.add_parser("cli", help="Configure bot via command line")
        parser.add_argument("infile", help="Path to file containing program input")
        parser.add_argument("--error-file", help="Path to error log", default=ERR_FILE)
        parser.add_argument(
            "--state-file",
            help="Path to state file.  This file tracks the last read input file line",
            default=STATE_FILE,
        )
        parser.add_argument(
            "--dry-run",
            help="Disables edits to the catalog",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-b",
            "--batch-size",
            help="Number of records to process at once",
            type=int,
            default=DEFAULT_BATCH_SIZE,
        )
        parser.add_argument(
            "-s",
            "--start-line",
            help="Start processing records starting from this line number of the input file",
            type=int,
            default=DEFAULT_START_LINE,
        )
        parser.add_argument(
            "-c",
            "--config",
            help="Path to Open Library client configuration file",
            type=str,
            default=None,
        )
        parser.set_defaults(func=start_job)

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(title="Commands")
    config_file_subparser(subparsers)
    command_line_subparser(subparsers)

    return parser


def configure_and_start(args):
    config_path = args.config

    if not Path(config_path).exists():
        print(f"{config_path} does not exist.")
        sys.exit(errno.ENOENT)

    config = ConfigParser()
    config.read(config_path)
    config_args = config["args"]

    args.infile = config_args.get("in_file", IN_FILE)
    args.state_file = config_args.get("state_file", STATE_FILE)
    args.error_file = config_args.get("error_file", ERR_FILE)
    args.dry_run = bool(config_args.get("dry_run", False))
    args.batch_size = config_args.getint("batch_size", DEFAULT_BATCH_SIZE)

    # Attempt to read starting line number from state file:
    state_path = Path(args.state_file)
    start_line = None
    if state_path.exists():
        with state_path.open("r") as f:
            line = f.readline()
            if line:
                start_line = int(line)

    args.start_line = (
        start_line
        if start_line
        else config_args.getint("start_line", DEFAULT_START_LINE)
    )

    start_job(args)


def start_job(args):
    infile_path = Path(args.infile)
    if not infile_path.exists():
        print(f"{infile_path} does not exist.")
        sys.exit(errno.ENOENT)

    ol = None
    try:
        ol_config = Config(config_file=args.config)
        ol = OpenLibrary(credentials=ol_config.get_config().get("s3", None))
    except Exception as err:
        print("Failed to initialize Open Library client.")
        print(f"Error: {err}")
        sys.exit(errno.ECONNREFUSED)

    # Initialize job and run
    results = FixPromiseItems(
        args.infile,
        args.state_file,
        args.error_file,
        ol=ol,
        batch_size=args.batch_size,
        start_line=args.start_line,
        dry_run=args.dry_run,
    ).run()

    print_summary(results, args.dry_run)

    print("Program terminated...")

def print_summary(results, dry_run):
    if dry_run:
        print("Running in dry-run mode.")
    print("Results:")
    print(f"Start line: {args.start_line}")
    print(f"Total records processed: {results.get('processed')}")
    print(f"Total modified: {results.get('modified')}")
    print(f"Total matched: {results.get('matched')}")
    print(f"Total errors: {results.get('errors')}")

if __name__ == "__main__":
    print("Starting...")
    parser = _parse_args()
    args = parser.parse_args()
    args.func(args)
