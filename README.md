# tteok

A small program that generates [Mochi](https://mochi.cards/) cards using
data from the National Institute of Korean Language's Korean Learners'
Dictionary (KrDict). It's called “tteok” because that's the Korean word
for "rice cake" (get it?).

## Setup

Install dependencies with:

```shell
pip install -r requirements.txt
```

You must also obtain an API key for the Korean Learners' Dictionary. Visit
[here](https://krdict.korean.go.kr/openApi/openApiRegister) after registering
an account to generate one (use Google Translate, if needed). Once you have
it, you can set it in your shell environment as follows:

```shell
KRDICT_API_KEY="<key>"
```

Or, you may pass it via the `--krdict-api-key` flag (if both are set, this
takes precedence).

## Creating a card

Suppose you want to create a card for the word “교통” . Simply run the following:

```shell
python3 tteok.py 교통
```

This will generate a card into `cards/` by default. You can override this default
location with the `--cards-dir` flag.

The format of the card is based on the [Mako](https://www.makotemplates.org/)
template defined in `templates/default.mako`. This can be overridden with the
`--card-template` flag. See [Card templates](#card-templates) for details on
the available template functions and variables.

## Creating multiple cards

You can also generate cards for multiple words at once. You can pass multiple
words as positional arguments:

```
python3 tteok.py 교통 기차 지하철
```

Or, have them read from a file using `--words-file`. This file should have one
word per line:

```
교통
기차
지하철
...
```

## Fetching cards

TODO

## Card templates

TODO
