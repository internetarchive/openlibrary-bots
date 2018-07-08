# Google Books search -> OL script
This script uses metadata from the Google Books API to create new books on Open Library.

## Python compatibility
This has only been tested against python3

## Installation
Install all Python Dependencies:
```
pip install -r requirements.txt
```
And follow [these instructions](https://developers.google.com/api-client-library/python/auth/api-keys) to create a Google API key + enable usage of the Google Books API.

## Usage
```
$ ./google_books_search.py --google_api_key <API key> --query "life of pi"

$ ./google_books_search.py --google_api_key <API key> --query 0547416113
```

## Examples
```bash
$ ./google_books_search.py --google_api_key <API key> --query "life of pi"
Google Books found 1619 results for this query. Here are the first 10:
	0: 'Life of Pi' by Yann Martel - ISBN 0547416113
	1: 'Life of Pi' by Yann Martel - ISBN 0151008116
	2: 'Life Of Pi Illustrated' by Yann Martel - ISBN 0857869035
	3: 'The High Mountains of Portugal' by Yann Martel - ISBN 0812997182
	4: 'The Making of Life of Pi' by Jean-Christophe Castelli - ISBN 006211414X
	5: 'Life of Pi  101 Amazingly True Facts You Didnt Know' by G Whiz - ISBN 1310919933
	6: 'Beatrice And Virgil may10' by Martel - ISBN 0670084514
	7: 'The Facts Behind the Helsinki Roccamatios' by Yann Martel - ISBN 0156032457
	8: 'Life of Pi Mit 1 AudioCD Level 4 A2B1' by Yann Martel - ISBN 3852729289
Which of these would you like to upload? 0
Traceback (most recent call last):
  File "./google_books_search.py", line 110, in <module>
    main()
  File "./google_books_search.py", line 106, in main
    _upload_ol_book(ol_books[chosen_index])
  File "./google_books_search.py", line 62, in _upload_ol_book
    raise ValueError("It looks like this book already exists on Open Library. "
ValueError: It looks like this book already exists on Open Library. This script doesn't yet support updating existing books -- sorry!
```

```bash
$ ./google_books_search.py --google_api_key <API key> --query "anatomy of a metahuman"
Google Books found 2804 results for this query. Here are the first 10:
	0: 'DC Comics Anatomy of a Metahuman' by S.D. Perry - ISBN 1608875016
	1: 'Constantine The Hellblazer Vol 1 Going Down' by Ming Doyle - ISBN 1401266762
	2: 'On a Sunbeam' by Tillie Walden - ISBN 1250178134
	3: 'Modern Masters Volume 17 Lee Weeks' by Tom Field - ISBN 1893905942
	4: 'Steppin Out' by Dan DiDio - ISBN 1401283373
	5: 'Heroes in the Night' by Tea Krulos - ISBN 1613747780
	6: 'The Once and Future Queen' by Adam P. Knave - ISBN 1506702503
	7: 'Wonder Woman Who Is Wonder Woman New Edition' by Allan Heinberg - ISBN 1401272339
	8: 'Injustice Gods Among Us Year Five Vol 1' by Brian Buccellato - ISBN 1401275613
Which of these would you like to upload? 0
Upload of OL26468269M successful!
```

If you search using an ISBN, and the results from the Google Books API is unambiguous, the script will skip the multiple-choice step:
```bash
$ ./google_books_search.py --google_api_key <API key> --query 0525522123
Upload of OL26468270M successful!
```
