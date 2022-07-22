# example invocation
# python CommaTheBot.py --file filtered_ol_dump_2022-06-06.txt.gz --limit 1

from olclient.bots import AbstractBotJob
import copy
import gzip
import re

class CommaTheBotJob(AbstractBotJob):
    pattern = None

    def __init__(self):
        super().__init__()
        articles = [
            '[Tt]he',
            '[Dd]er', '[Dd]ie', '[Dd]as',
            '[Ll]e', '[Ll]a', '[Ee]l',
            '[Ll]os', '[Ll]as', '[Ll]es',
        ]

        self.pattern = re.compile(rf"^([\w ,]*), ?({'|'.join(articles)})$")

    def needs_fixing(self, edition_title: str) -> bool:
        if edition_title is None: return False # no title given

        return True if(self.pattern.search(edition_title)) else False

    def fix_title(self, edition_title: str) -> str:
        match = self.pattern.search(edition_title)

        return f"{match.group(2)} {match.group(1)}"

    def run(self) -> None:
        self.dry_run_declaration()

        comment = 'foo, the -> the foo'
        with gzip.open(self.args.file, 'rb') as file:
            for row in file:
                row, json_data = self.process_row(row)
                if not self.needs_fixing(json_data.get('title')): # .get() to avoid KeyError
                    continue

                # the database may have changed since the dump was created, so call the OpenLibrary API and check again
                olid = json_data['key'].split('/')[-1]
                isEdition = json_data['type']['key'] == '/type/edition'
                book = self.ol.Edition.get(olid) if isEdition else self.ol.Work.get(olid)

                if not ( book.type['key'] == '/type/edition' or book.type['key'] == '/type/work' ):
                    continue # skip deleted books
                if not self.needs_fixing(book.title):
                    continue

                # this book needs fixing
                old_title = copy.deepcopy(book.title)
                book.title = self.fix_title(book.title)

                self.logger.info(f'{olid}: "{old_title}" -> "{book.title}"')
                self.save(lambda: book.save(comment=comment))


if __name__ == "__main__":
    job = CommaTheBotJob()

    try:
        job.run()
    except Exception as e:
        job.logger.exception("")
        raise e
