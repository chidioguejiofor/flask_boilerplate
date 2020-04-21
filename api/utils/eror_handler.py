from marshmallow import ValidationError
from api.utils.exceptions import ModelOperationException, ResponseException
from api.utils.messages.error import serialization_error


def error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_errors(error):
        if '_schema' in error.messages:
            error.messages = error.messages['_schema']
        return {
            'errors': error.messages,
            'message': serialization_error['invalid_fields']
        }, 400

    @app.errorhandler(ModelOperationException)
    def handle_data_conflict(e):
        return {'message': e.message}, e.status_code

    @app.errorhandler(ResponseException)
    def handle(e):  #
        return {'message': e.message}, e.status_code
