import argparse
from os import error
from pathlib import Path
import csv
import re
from typing import Set, List, Union
import typing


def pattern_to_regex(pattern: str) -> str:
    r'''
    Converts an `autotag` lexicon pattern into a regular expression string.

    The pattern syntax is:
    1. `[...]` -- a character class that matches exactly one character.
       Within the class a `\` escapes the next character, e.g. `[\]]`
       matches `]`.
    2. `*` straight after a character class -- zero or more characters from
       that class, e.g. `[0-9]*`.
    3. `*` anywhere else -- zero or more of any character (`.*`).
    4. Every other character is literal and is escaped.

    # Parameters

    pattern : `str`
        The `autotag` `lemma` or `pos` pattern.

    # Returns

    `str`

    # Raises

    ValueError
        If a `[` does not start a closed, non-empty character class.
    '''
    regex = ''
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == '[':
            # Find the first `]` that is not escaped by a `\`.
            closing_index = -1
            class_index = index + 1
            while class_index < len(pattern):
                if pattern[class_index] == '\\':  # '\\' is a single backslash character.
                    class_index += 2
                    continue
                if pattern[class_index] == ']':
                    closing_index = class_index
                    break
                class_index += 1
            if closing_index == -1:
                raise ValueError(f'The `[` at position {index} in the pattern '
                                 f'`{pattern}` does not have a closing `]`.')
            if closing_index == index + 1:
                raise ValueError(f'The character class at position {index} in the '
                                 f'pattern `{pattern}` is empty.')
            regex += pattern[index:closing_index + 1]
            index = closing_index + 1
            if index < len(pattern) and pattern[index] == '*':
                regex += '*'
                index += 1
            continue
        if character == '*':
            regex += '.*'
        else:
            regex += re.escape(character)
        index += 1
    return regex


def check_autotag_pattern(field_name: str, pattern: str) -> None:
    '''
    Raises a `ValueError` if the `autotag` `pattern` cannot be converted
    into a valid regular expression, or if it is a `pos` pattern of only `*`.

    # Parameters

    field_name : `str`
        The name of the field the pattern comes from, e.g. `lemma` or `pos`.

    pattern : `str`
        The `autotag` pattern.

    # Raises

    ValueError
        If the pattern is not valid.
    '''
    if field_name == 'pos' and pattern.strip() == '*':
        raise ValueError('The `pos` value of an `autotag` entry cannot be just '
                         '`*`, every `autotag` entry needs a POS pattern.')
    try:
        # The `^` and `$` are not needed to check that the pattern is valid, they
        # show that an autotag pattern has to match the whole lemma/POS value,
        # e.g. `*kph` matches `100kph` but not `kphs`.
        re.compile('^' + pattern_to_regex(pattern) + '$')
    except re.error as regex_error:
        raise ValueError(f'The `{field_name}` pattern `{pattern}` is not a valid '
                         f'pattern: {regex_error}')


def check_file(file_type: str, lexicon_collection_file: Path) -> None:
    '''
    Will raise a `ValueError` if the `lexicon_collection_file` is not formatted 
    correctly. 

    # Parameters

    file_type : `str`
        Type of the file can be one of the following values:
        1. `single` -- single lexicon files.
        2. `autotag` -- autotag lexicon files, these are single lexicon files
           whereby the `lemma` and `pos` fields are patterns, these patterns
           are checked to ensure that they are valid and that the `pos`
           pattern is not only `*`.
        3. `mwe` -- multi word expresion lexicon files.

    lexicon_collection_file : `Path`
        File path to the lexicon file.

    # Raises

    ValueError
        If the `lexicon_collection_file` is not formatted correctly. The three main
        sources of this error: 1. When the TSV field does not contain a header with
        the minimum field names for the type of file, 2. When a row does not contain
        enough tab separated values, 3. When the field values in the row does
        not contain a string value when it should.
    '''

    minimum_field_names = {'lemma', 'semantic_tags'}
    if file_type == 'autotag':
        minimum_field_names = {'lemma', 'pos', 'semantic_tags'}
    if file_type == 'mwe':
        minimum_field_names = {'mwe_template', 'semantic_tags'}
    extra_field_names = ['pos', 'token']
    if file_type == 'mwe':
        extra_field_names = []
    field_names_to_extract = []

    with lexicon_collection_file.open('r', newline='') as lexicon_data:
        csv_reader = csv.DictReader(lexicon_data, delimiter='\t')
        file_field_names: Set[str] = set()
        if csv_reader.fieldnames is not None:
            file_field_names = set(csv_reader.fieldnames)
        if minimum_field_names.issubset(file_field_names):
            field_names_to_extract.extend(list(minimum_field_names))
        else:
            header_error_message = (f"The TSV file {str(lexicon_collection_file)} should "
                                    "contain a header that has as minimum the following fields "
                                    f"{minimum_field_names}. The field names found "
                                    f"were {file_field_names}")
            raise ValueError(header_error_message)
        
        for extra_field_name in extra_field_names:
            if extra_field_name in file_field_names:
                field_names_to_extract.append(extra_field_name)

        for row_index, row in enumerate(csv_reader):
            general_error_message = '\n' + ('-' * 50) + '\n\n'
            general_error_message += (f'The Error occurred on row {row_index} '
                                      f'within the lexicon File: {str(lexicon_collection_file)}\n '
                                      f'Line contains: \n{row}\n\n')
            try:
                if None in row.keys():
                    row_header_error_message = ('This row contains an extra field that does'
                                                ' not have a header name associated to it.'
                                                ' This is represented by the `None` key in '
                                                'the row data.\n\n')
                    raise ValueError(general_error_message + row_header_error_message + '-' * 50)
                row_data: typing.MutableMapping[str, Union[str, List[str]]] = {}
                for field_name in field_names_to_extract:
                    if not isinstance(row[field_name], str):
                        field_value_error = (f'The value within the header {field_name}'
                                             f' should be of type `str` and not {type(row[field_name])}'
                                             f', the value is: {row[field_name]}.\n\n')
                        raise ValueError(general_error_message + field_value_error + '-' * 50)
                    if field_name == 'semantic_tags':
                        row_data[field_name] = row[field_name].split()
                    else:
                        row_data[field_name] = row[field_name]
                if file_type == 'autotag':
                    for field_name in ['lemma', 'pos']:
                        try:
                            check_autotag_pattern(field_name, row[field_name])
                        except ValueError as pattern_error:
                            raise ValueError(general_error_message + f'{pattern_error}\n\n' + '-' * 50)
            except ValueError as value_error:
                raise value_error
            except:
                raise Exception(general_error_message + '-' * 50)
                

if __name__ == '__main__':
    description = '''
    A file checker for single word, autotag, and multi word expression lexicon files.
    This file checker checks the following;

    1. The minimum header names exist,
    2. All fields/columns have a header name,
    3. All lines contain the minimum information e.g. no comment lines exist
    in the middle of the file.
    4. For autotag files, the `lemma` and `pos` patterns are valid and the
    `pos` pattern is not only `*`.
    '''
    file_type_help = ('single for single word lexicon file format, '
                      'autotag for autotag lexicon file format, or '
                      'mwe for multi word expression file format')
    parser = argparse.ArgumentParser()
    parser.add_argument('lexicon_file_path', type=Path,
                        help='File path to the lexicon file to check')
    parser.add_argument('file_type', type=str, choices=['single', 'autotag', 'mwe'],
                        help=file_type_help)
    args = parser.parse_args()

    check_file(args.file_type, args.lexicon_file_path)
