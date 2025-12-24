import random


def handler(event, context):
    # random logic to illustrate returning an object (to include hints when a check fails) or a boolean
    if random.randint(1, 10) % 2 == 0:
        return {
            "result": random.randint(1, 10) % 2 == 0,
            "hint_message": "This <strong>Hint message</strong> appears when the <code>result</code> is <code>False</code>. <code>hint_message</code> and <code>hint_reference</code> are optional and either may be omitted.",
        }
    return True
