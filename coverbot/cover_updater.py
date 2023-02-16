"""
Adds a cover to a coverless edition if it has an ocaid
NOTE: This script assumes the Open Library Dump passed only contains coverless editions with an ocaid
"""

import gzip
import json

from olclient import AbstractBotJob


class AddInternetArchiveCoverJob(AbstractBotJob):
    def run(self) -> None:
        """Add the Internet Archive scan to applicable coverless edition."""
        self.write_changes_declaration()
        with gzip.open(self.args.file, "rb") as fin:
            header = {"type": 0, "key": 1, "revision": 2, "last_modified": 3, "JSON": 4}
            for row in fin:
                row = row.decode().split("\t")
                _json = json.loads(row[header["JSON"]])
                olid = _json["key"].split("/")[-1]
                edition_obj = self.ol.Edition.get(olid)
                covers = getattr(edition_obj, "covers", [])
                if not self.valid_covers(covers):
                    cover_url = (
                        f"https://archive.org/download/{_json['ocaid']}/page/cover"
                    )
                    self.logger.info(f"{edition_obj.olid} {covers} {cover_url}")
                    self.save(lambda: edition_obj.add_bookcover(cover_url=cover_url))

    @staticmethod
    def valid_covers(covers: list) -> bool:
        return covers not in ([], [-1], [None], [-1, None], [None, -1])


if __name__ == "__main__":
    job = AddInternetArchiveCoverJob()

    try:
        job.run()
    except Exception as e:
        job.logger.exception(e)
        raise e
