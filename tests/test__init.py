"""Module to test for the flask application"""

import json


def test__flask_application(client):
    """Should pass if the application starts successfully.
	Args:
		client (func): Flask test client
	Returns:
		None
	"""

    response_raw = client.get('/')
    response_json = json.loads(response_raw.data)
    assert response_json == {
        'data': {
            'message': 'API service is healthy, Goto to /api/',
            'status': 'success'
        }
    }
