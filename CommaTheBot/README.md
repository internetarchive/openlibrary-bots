# CommaTheBot

A bot intended to fix titles like "foo, the" by moving the "the" to the start ("the foo").

Currently searches for the following articles (with starting upper- and lowercase letter):
`The`, `Der`, `Die`, `Das`, `Le`, `La`, `El`, `Los`, `Las`, `Les`

"Home" repo: https://github.com/bsvka/CommaTheBot

## All types dump 2022-06-06 stats

| Total    | Found | %         |
| -------- | ----- | --------- |
| 72819552 | 25430 | 0.0349219 |

## Running It
You need `curl`, `zgrep` and `pv` installed on your system.

Start the `main.sh` file. It will set-up a venv, auto-install all dependencies into it, download the altest dump, pre-filter that and finally run the bot itself. All options you pass to `main.sh` will be passed to `CommaTheBot.py`. run `python CommaTheBot.py -h` to find out what options are available. You don't have to pass `--file|-f`.

## How it works
The detection of articles appended to the title with a comma is done via the below [regular expression](https://en.wikipedia.org/wiki/Regular_expression).

As of 2022-07-20 the full pattern is the following:  
`^([\\w ,]*), ?([Tt]he|[Dd]er|[Dd]ie|[Dd]as|[Ll]e|[Ll]a|[Ee]l|[Ll]os|[Ll]as|[Ll]es)$`

Paste it into [regex101.com](https://regex101.com/) for a plain english explanation of how it works.