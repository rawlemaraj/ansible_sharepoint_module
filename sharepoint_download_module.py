#!/usr/bin/python

import os
import requests
from ansible.module_utils.basic import AnsibleModule

def download_file(module, file_url, username, password):
    response = requests.get(file_url, auth=(username, password), verify=False)

    if response.status_code == 200:
        filename = file_url.split('/')[-1]  # Extract filename from URL
        local_path = os.path.join(os.getcwd(), filename)
        with open(local_path, 'wb') as f:
            f.write(response.content)
        return local_path
    else:
        module.fail_json(msg='Failed to download file from SharePoint.')

def main():
    module = AnsibleModule(
        argument_spec=dict(
            file_url=dict(type='str', required=True),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True)
        )
    )

    file_url = module.params['file_url']
    username = module.params['username']
    password = module.params['password']

    try:
        local_path = download_file(module, file_url, username, password)
        result = dict(
            changed=True,
            local_path=local_path
        )
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
