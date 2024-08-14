import json
import os
import re
import subprocess

import automatic_code_review_commons as commons


def review(config):
    path_source = config['path_source']
    regex_ignore = config['regexIgnore']

    comments = []

    for raiz, _, arquivos in os.walk(path_source):
        for arquivo in arquivos:
            if not arquivo.endswith(".h"):
                continue

            header_file = os.path.join(raiz, arquivo)

            if __is_regex_ok(regex_ignore, header_file):
                continue

            data = subprocess.run(
                f'ctags -R --output-format=json --languages=c++ --fields=+an --c++-kinds=+p {header_file}',
                shell=True,
                capture_output=True,
                text=True,
            ).stdout

            errors = []
            class_line = None

            for data_obj in data.split('\n'):
                if data_obj == '':
                    continue

                obj = json.loads(data_obj)

                if obj['kind'] == 'class':
                    class_line = obj['line']

                if obj['kind'] != 'function':
                    continue

                if 'template<typename T>' in obj['pattern']:
                    continue

                errors.append(obj)

            if class_line is not None:
                template_line = class_line - 1

                with open(header_file, 'r') as content:
                    lines = content.readlines()
                    for line_number in [template_line - 1, class_line - 1]:
                        code = lines[line_number]
                        if "template <" in code or "template<" in code:
                            errors = []

            if len(errors) > 0:
                methods = []
                for error in errors:
                    methods.append(error['name'])

                relative_path = header_file.replace(path_source, "")[1:]

                description_message = config['message']
                description_message = description_message.replace("${FILE_PATH}", relative_path)
                description_message = description_message.replace("${METHODS}", ", ".join(methods))

                comments.append(commons.comment_create(
                    comment_id=commons.comment_generate_id(relative_path),
                    comment_path="",
                    comment_description=description_message,
                    comment_snipset=False,
                ))

    return comments


def __is_regex_ok(regex_list, text):
    for regex in regex_list:
        if re.match(regex, text):
            return True

    return False
