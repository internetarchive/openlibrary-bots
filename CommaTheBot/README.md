# CommaTheBot

A bot intended to fix titles like "foo, the" by moving the "the" to the start ("the foo").
"Home" repo: https://github.com/bsvka/CommaTheBot

Currently searches for the following articles (with starting upper- and lowercase letter):
`The`, `Der`, `Die`, `Das`, `Le`, `La`, `El`, `Los`, `Las`, `Les`

Feel free to recommend more.
Here is a list of possible ones which I haven't yet added. If you recognize any of these as valid, let me know.
| No. of Occ. | Article |
| ----------- | ------- |
| 4594        | A       |
| 2961        | O       |
| 875         | Pa      |
| 611         | Os      |
| 571         | Set     |
| 502         | I       |
| 478         | Va      |
| 435         | As      |
| 433         | a       |
| 384         | Ky      |
| 357         | Mo      |
| 293         | An      |
| 246         | Ga      |
| 242         | Um      |
| 212         | Y       |
| 204         | PA      |
| 194         | Me      |
| 182         | hoy     |

The above articles have been found via `article_finder.py` and `countsort.sh` (both only found in the "Home" repo).


## All types dump 2022-06-06 stats

| Total    | Found | %         |
| -------- | ----- | --------- |
| 72819552 | 25430 | 0.0349219 |


## Running It

You need `curl`, `zgrep` and `pv` installed on your system.

Start the `main.sh` file. It will set-up a venv, auto-install all dependencies into it, download the altest dump, pre-filter that and finally run the bot itself. All options you pass to `main.sh` will be passed to `CommaTheBot.py`. run `python CommaTheBot.py -h` to find out what options are available. You don't have to pass `--file|-f`.


## How it works

The detection of articles appended to the title with a comma is done via the below [regular expression](https://en.wikipedia.org/wiki/Regular_expression).

As of 2022-07-23 the full pattern is the following:
`^([\\w ,]+), ?([Tt]he|[Dd]er|[Dd]ie|[Dd]as|[Ll]e|[Ll]a|[Ee]l|[Ll]os|[Ll]as|[Ll]es)$`

Paste it into [regex101.com](https://regex101.com/) for a plain english explanation of how it works.
