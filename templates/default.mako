# ${word}
「${part_of_speech} 」
% if pronunciations:
[ ${", ".join(pronunciations)} ]
% endif
<speech voice="ko-KR-Wavenet-D">${word}</speech>
---
% if hanja:
# ${hanja}
    % for comp in hanja_components:
[${comp['character']}](https://en.wiktionary.org/wiki/${comp['character']}): {{${', '.join(comp['readings'])}}}
    % endfor
---
% endif
% for i, definition in enumerate(definitions, start=1):
${i}. ${definition['definition']}
    % if definition['translated_definition']:
{{${definition['translated_definition']}}}
    % endif
    % if definition['translated_word']:
{{*${definition['translated_word']}*}}
    % endif
    % if definition['sentence_patterns']:
> ${', '.join(definition['sentence_patterns'])}
    % endif
    % for phrase in definition['example_phrases'][:3]:
* ${phrase.replace(word, f'**{word}**')}
    % endfor
    % for sentence in definition['example_sentences'][:1]:
* ${sentence.replace(word, f'**{word}**')}
    % endfor
    % for segment in definition['example_conversation'][:2]:
* ${segment.replace(word, f'**{word}**')}
    % endfor
---
% endfor
