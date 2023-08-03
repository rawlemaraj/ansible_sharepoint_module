#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from requests import Session
from requests_ntlm import HttpNtlmAuth
import json

def run_module():
    module_args = dict(
        sharepoint_url=dict(type='str', required=True),
        site_url=dict(type='str', required=True),
        folder_path=dict(type='str', required=True),
        local_file_path=dict(type='str', required=True),
        remote_file_name=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Ensure requests are made securely
    session = Session()
    session.auth = HttpNtlmAuth(module.params['username'], module.params['password'])

    # Fetch form digest value
    contextinfo_url = f"{module.params['sharepoint_url']}/{module.params['site_url']}/_api/contextinfo"
    contextinfo_response = session.post(contextinfo_url, headers={'Accept': 'application/json;odata=verbose'}, verify=False)
    contextinfo = contextinfo_response.json()
    form_digest_value = contextinfo['d']['GetContextWebInformation']['FormDigestValue']

    # URL to the folder where you want to upload the file
    upload_url = f"{module.params['sharepoint_url']}/{module.params['site_url']}/_api/web/GetFolderByServerRelativeUrl('{module.params['folder_path']}')/Files/add(url='{module.params['remote_file_name']}',overwrite=true)"

    # Read the file data
    with open(module.params['local_file_path'], 'rb') as file_data:
        file_contents = file_data.read()

    # Set headers and make the POST request
    headers = {
        'Content-Type': 'application/octet-stream',
        'Accept': 'application/json;odata=verbose',
        'X-RequestDigest': form_digest_value,
    }
    response = session.post(upload_url, headers=headers, data=file_contents, verify=False)

    # Check the result
    if response.status_code == 200:

        # Parse the response to get the server-relative URL of the uploaded file
        response_json = response.json()
        file_server_relative_url = response_json['d']['ServerRelativeUrl']

        # URL to check in the uploaded file
        checkin_url = f"{module.params['sharepoint_url']}/{module.params['site_url']}/_api/web/GetFileByServerRelativeUrl('{file_server_relative_url}')/CheckIn(comment='Checked in by script', checkintype=0)"

        # Make the POST request to check in the file
        response = session.post(checkin_url, headers={'Accept': 'application/json;odata=verbose', 'X-RequestDigest': form_digest_value}, verify=False)

        if response.status_code == 200:
            module.exit_json(changed=True, message="File uploaded and checked in successfully.")
        else:
            module.fail_json(msg="Failed to check in file.", error_details=response.text)
    else:
        module.fail_json(msg="Failed to upload file.", error_details=response.text)


def main():
    run_module()


if __name__ == '__main__':
    main()
