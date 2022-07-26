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


def get_words_by_subject_category(cat):
    word_ids = []
    for page in range(1, 1000):
        response = krdict.scraper.fetch_subject_category_words(
            category=krdict.SubjectCategory.get(cat),
            page=page,
            per_page=100,
        )
        results = response['data']['results']
        for result in results:
            word_id = result['target_code']
            word_ids.append(word_id)
        if len(results) < 100:
            break
    return word_ids


def get_words_by_meaning_category(cat):
    word_ids = []
    for page in range(1, 1000):
        response = krdict.scraper.fetch_meaning_category_words(
            category=krdict.MeaningCategory.get(cat),
            page=page,
            per_page=100,
        )
        results = response['data']['results']
        for result in results:
            word_id = result['target_code']
            word_ids.append(word_id)
        if len(results) < 100:
            break
    return word_ids


def get_word_matches(word):
    matches = []
    for page in range(1, 1000):
        response = krdict.advanced_search(
                query=word,
                search_type='word',
                search_method='exact',
                page=page,
                per_page=100,
                translation_language='english',
                raise_api_errors=True,
        )
        results = response['data']['results']
        for result in results:
            match = result['target_code']
            matches.append(match)
        if len(results) < 100:
            break
    return matches


def get_card(word_data, card_template):
    templ = Template(card_template, output_encoding='utf-8')
    buf = io.StringIO()
    ctx = Context(buf, **word_data)
    templ.render_context(ctx)

    return buf.getvalue()


def get_word_data(word_id):
    response = krdict.view(
        target_code=word_id,
        translation_language='english',
        guarantee_keys=True,
        raise_api_errors=True,
        options={
            'use_scraper': True,
        }
    )
    word_data = format_krdict_view(response)
    return word_data


def format_krdict_view(response):
    word_info = response['data']['results'][0]['word_info']
    hanja, hanja_components = format_krdict_view_hanja(word_info)
    card_data = {
        'word':             word_info['word'],
        'part_of_speech':   word_info['part_of_speech'],
        'hanja':            hanja,
        'hanja_components': hanja_components,
        'definitions':      format_krdict_view_defns(word_info),
        'pronunciations':   format_krdict_view_prons(word_info),
    }
    return card_data


def format_krdict_view_hanja(word_info):
    hanja = ''
    hanja_components = []
    for lang_info in word_info['original_language_info']:
        if lang_info['language_type'] == '한자':
            hanja = lang_info['original_language']
            for hanja_info in lang_info.get('hanja_info', []):
                hanja_component = {
                    'character': hanja_info['hanja'],
                    'readings':  hanja_info['readings'],
                }
                hanja_components.append(hanja_component)
            break
    return (hanja, hanja_components)


def format_krdict_view_defns(word_info):
    if 'definition_info' not in word_info:
        return []
    defns = []
    for defn_info in word_info['definition_info']:
        defn = format_krdict_view_defn(defn_info)
        defns.append(defn)
    return defns


def format_krdict_view_defn(defn_info):
    defn = {
        'definition': defn_info.get('definition'),
        'translated_definition': None,
        'translated_word': None,
        'sentence_patterns': [],
        'example_sentences': [],
        'example_phrases': [],
        'example_conversation': [],
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
            defn['translated_word'] = trns_info.get('word')
            defn['translated_definition'] = trns_info['definition']
            break
    if 'pattern_info' in defn_info:
        for pat_info in defn_info['pattern_info']:
            defn['sentence_patterns'].append(pat_info['pattern'])
    if 'example_info' in defn_info:
        # NOTE: Some responses didn't have this key set
        # even with the 'guarantee_keys' option specified
        # in the request.
        for ex_info in defn_info['example_info']:
            example = ex_info['example']
            if ex_info['type'] == '문장':
                defn['example_sentences'].append(example)
            if ex_info['type'] == '대화':
                defn['example_conversation'].append(example)
            if ex_info['type'] == '구':
                defn['example_phrases'].append(example)

    return defn


def format_krdict_view_prons(word_info):
    if 'pronunciation_info' not in word_info:
        return []
    prons = []
    for pron_info in word_info['pronunciation_info']:
        prons.append(pron_info.get('pronunciation', ''))

    return prons


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('words',
                        nargs='*', metavar='WORD',
                        help='word for which to generate card files')
    parser.add_argument('--krdict-api-key',
                        help="API key for the Korean Learners' Dictionary API")
    parser.add_argument('--subject-category',
                        help='generate cards for words of a specific subject category')
    parser.add_argument('--meaning-category',
                        help='generate cards for words of a specific meaning category')
    parser.add_argument('--words-file',
                        type=argparse.FileType('r'),
                        help='file of words (one line per word) for which to generate card files')
    parser.add_argument('--card-template',
                        default='templates/default.mako',
                        type=argparse.FileType('r'),
                        help='file containing Mako template for cards')
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

    word_ids = []

    if args.subject_category:
        word_ids = get_words_by_subject_category(args.subject_category)
    elif args.meaning_category:
        word_ids = get_words_by_meaning_category(args.meaning_category)
    else:
        words = []
        if args.words:
            words = args.words
        if args.words_file:
            words = args.words_file.read().splitlines()
        for word in words:
            for word_id in get_word_matches(word):
                word_ids.append(word_id)

    card_template = args.card_template.read()

    print(f'Generating cards for {len(word_ids)} words')

    for i, word_id in enumerate(word_ids, start=1):
        word_data = get_word_data(word_id)
        word = word_data['word']
        card = get_card(word_data, card_template)
        card_file_path = os.path.join(args.cards_dir, f'{word}_{word_id}.md')
        card_file = open(card_file_path, 'w+', encoding='utf-8')
        card_file.write(card)
        card_file.close()
        print(f'Card generated for {word} [{word_id}] ({i}/{len(word_ids)})')
