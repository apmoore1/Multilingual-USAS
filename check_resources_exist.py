import json
import sys
from pathlib import Path
from typing import Dict, List

if __name__ == '__main__':
    json_data = Path(__file__, '..', 'language_resources.json').resolve()
    repository_folder = json_data.parent
    with json_data.open('r') as json_fp:
        data = json.load(json_fp)

    missing: List[str] = []
    for language_code, meta_data in data.items():
        resources: List[Dict[str, str]] = meta_data['resources']
        for resource in resources:
            resource_file_path = Path(repository_folder, resource['file path'])
            if not resource_file_path.is_file():
                missing.append(f'{language_code} ({resource["data type"]}): '
                               f'{resource["file path"]}')

    if missing:
        print('The following files listed in language_resources.json do not '
              'exist:')
        for line in missing:
            print(f'  {line}')
        sys.exit(1)
    print('All files listed in language_resources.json exist.')
