import random


def handler(event, context):
    # random logic to illustrate returning an object (to include hints when a check fails) or a boolean
    if random.randint(1, 10) % 2 == 0:
        return {
            "result": random.randint(1, 10) % 2 == 0,
            "hint_message": "This <strong>Hint message</strong> appears when the <code>result</code> is <code>False</code>. <code>hint_message</code> and <code>hint_reference</code> are optional and either may be omitted.",
            "hint_reference": "https://cloudacademy.com/library/",
        }
    return True


"""
Example event objects before and after template outputs are available (BlueIp is a template output in this example)

print(event) # before lab setup is complete - provisioning_block_outputs is None
{
    'step_variables': {
        '?UserName': 'ec2-user',
        'BlueIp': "{{BlueIp|default:'wait-for-lab-setup-to-complete'}}",
        'context': {
            'laboratory_id': 914,
            'lab_session_id': 1136803,
            'lab_step_id': 2244,
            'lab_step_session_id': 6401867},
            'lab_session_start_datetime': '2022-01-24T17:00:00'
        },
        'provisioning_block_outputs': None,
        'cloud_environment_setup_status': None
    },
    'provisioning_block_outputs': None,
    'region_id': 'us-west-2',
    'credentials': {
        'credential_id': 'AKIAVLDOLB0123456789',
        'credential_key': 'rpHGQVmESS7PQdrW0/qqiiAB7eMvHl0123456789'
    },
    'environment_params': {}
}

print(event) # after lab setup is complete - provisioning_block_outputs is a dictionary
{
    'step_variables': {
        '?UserName': 'ec2-user',
        'BlueIp': "{{BlueIp|default:'wait-for-lab-setup-to-complete'}}",
        'context': {
            'laboratory_id': 914,
            'lab_session_id': 1136803,
            'lab_step_id': 2244,
            'lab_step_session_id': 6401867,
            'lab_session_start_datetime': '2022-01-24T17:00:00'
        },
        'provisioning_block_outputs': {
            'BlueIp': {
                'key': 'BlueIp',
                'description': None,
                'value': '35.165.5.169',
                'name': None
            }
        },
        'cloud_environment_setup_status': None
    },
    'provisioning_block_outputs': {
        'BlueIp': {
            'key': 'BlueIp',
            'description': None,
            'value': '35.165.5.169',
            'name': None
        }
    },
    'region_id': 'us-west-2',
    'credentials': {
        'credential_id': 'AKIAVLDOLB0123456789',
        'credential_key': 'rpHGQVmESS7PQdrW0/qqiiAB7eMvHl0123456789'
    },
    'environment_params': {}
}
"""
