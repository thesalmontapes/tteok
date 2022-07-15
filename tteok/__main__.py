import os
import sys
import io
import argparse

import krdict
from mako.template import Template
from mako.runtime import Context

krdict_api_key = os.environ.get("KRDICT_API_KEY")

ERR_MISSING_KRDICT_API_KEY = (
    "An API key for the Korean Learners' Dictionary should be set with "
    "KRDICT_API_KEY or --krdict-api-key. You can obtain one with an "
    "account from https://krdict.korean.go.kr/openApi/openApiInfo."
)

DEFAULT_MOCHI_CARD_TEMPLATE = """# ${word}
---
% if hanja:
# ${hanja}
---
% endif
<speech voice="ko-KR-Wavenet-D">${word}</speech>
% for i, definition in enumerate(definitions, start=1):
${i}. ${definition['korean']}
    % if 'english' in definition:
      Translation: {{${definition['english']}}}
    % endif
    % if 'english_words' in definition:
      Equivalent(s): {{${definition['english_words']}}}
    % endif
% endfor
"""


def get_word_matches(word):
    response = krdict.advanced_search(
            query=word,
            search_type='word',
            search_method='exact',
            sort='popular',
            per_page=100,
            translation_language='english',
            raise_api_errors=True,
    )
    matches = []
    for result in response['data']['results']:
        match = result['target_code']
        matches.append(match)

    return matches


def get_card(word_id, card_template):
    card_data = get_card_data(word_id)
    templ = Template(card_template, output_encoding='utf-8')
    buf = io.StringIO()
    ctx = Context(buf, **card_data)
    templ.render_context(ctx)

    return buf.getvalue()


def get_card_data(word_id):
    response = krdict.view(
        target_code=word_id,
        translation_language='english',
        guarantee_keys=True,
        raise_api_errors=True,
    )
    card_data = format_krdict_view(response)
    return card_data


def format_krdict_view(response):
    word_info = response['data']['results'][0]['word_info']
    card_data = {
        'word':        word_info['word'],
        'hanja':       format_krdict_view_hanja(word_info),
        'definitions': format_krdict_view_defns(word_info['definition_info']),
    }
    return card_data


def format_krdict_view_hanja(word_info):
    for lang_info in word_info['original_language_info']:
        if lang_info['language_type'] == '한자':
            return lang_info['original_language']


def format_krdict_view_defns(defn_infos):
    defns = []
    for defn_info in defn_infos:
        defn = format_krdict_view_defn(defn_info)
        defns.append(defn)
    return defns


def format_krdict_view_defn(defn_info):
    defn = {
        'korean': defn_info.get('definition'),
    }
    if 'translations' in defn_info:
        # NOTE: Some responses didn't have this key set
        # even with the 'guarantee_keys' option specified
        # in the request.
        for trns_info in defn_info['translations']:
            if trns_info['language'] != '영어':
                continue
            # Not sure if there can be more than one
            # translation for a single language; in
            # any case, one should suffice so just
            # grab the first.
            defn['english_words'] = trns_info.get('word')
            defn['english'] = trns_info['definition']
            break

    return defn


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('words',
                        nargs='+', metavar='WORD',
                        help='word for which to generate card files')
    parser.add_argument('--krdict-api-key',
                        help="API key for the Korean Learners' Dictionary API")
    parser.add_argument('--cards-dir',
                        default='cards',
                        help='directory to output card files')
    args = parser.parse_args()

    if args.krdict_api_key:
        krdict_api_key = args.krdict_api_key
    if not krdict_api_key:
        sys.exit(ERR_MISSING_KRDICT_API_KEY)
    krdict.set_key(krdict_api_key)

    os.makedirs(args.cards_dir, exist_ok=True)

    for word in args.words:
        matches = get_word_matches(word)
        for i, match in enumerate(matches, start=1):
            card = get_card(match, DEFAULT_MOCHI_CARD_TEMPLATE)
            card_file_path = os.path.join(args.cards_dir, f'{word}_{i}.md')
            card_file = open(card_file_path, 'w+', encoding='utf-8')
            card_file.write(card)
            card_file.close()
            print(f'Card generated for {word} [{i}]')
