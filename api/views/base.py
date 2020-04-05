from flask_restplus import Resource
from .decorators import Authentication, classproperty


class BaseView(Resource):
    PROTECTED_METHODS = []

    @classproperty
    def method_decorators(self):
        return [Authentication(self)]
