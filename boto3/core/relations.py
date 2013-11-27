import boto3
from boto3.core.exceptions import NoSuchRelationError
from boto3.core.proxy import Proxy


class BaseRelation(object):
    is_relation = True

    def __init__(self, related_class_name, var_name, required=False):
        self.related_class = None
        self.parent = None

        self.related_class_name = related_class_name
        self.var_name = var_name
        self.required = required

    def __str__(self):
        return '{0}: {1} to {2}'.format(
            self.__class__.__name__,
            self.var_name,
            self.related_class_name
        )

    def add_to_instance(self, parent):
        self.parent = parent
        self.parent._relations[self.var_name] = self

    def remove_from_instance(self):
        self.parent = None
        # If we were already somehow previously removed, silently pass.
        self.parent._relations.pop(self.var_name, None)

    def get_session(self):
        if not self.parent:
            return boto3.session

        if not hasattr(self.parent, '_details'):
            return boto3.session

        if not getattr(self.parent._details, 'session', None):
            return boto3.session

        return self.parent._details.session

    def construct_related_class(self):
        raise NotImplementedError(
            "Subclasses must implement this method."
        )

    def update_with_identifier(self, kwargs):
        # More bleh.
        var_name = self.parent._details.identifier_var_name
        kwargs[var_name] = self.parent.get_identifier()
        return kwargs

    def fetch(self, **kwargs):
        klass = self.construct_related_class()
        instance = klass(connection=self.parent._connection)
        proxy = Proxy(
            target=instance,
            kwargs=self.update_with_identifier(kwargs)
        )
        return proxy


class OneToOne(BaseRelation):
    is_one_to_one = True

    def construct_related_class(self):
        if not self.related_class:
            session = self.get_session()
            # Bleh.
            self.related_class = session.get_resource(
                self.parent._details.service_name,
                self.related_class_name
            )

        return self.related_class


class OneToMany(BaseRelation):
    is_one_to_many = True

    def construct_related_class(self):
        if not self.related_class:
            session = self.get_session()
            # Bleh.
            self.related_class = session.get_collection(
                self.parent._details.service_name,
                self.related_class_name
            )

        return self.related_class


class RelationsHandler(object):
    mapping = {
        "1-1": OneToOne,
        "1-M": OneToMany,
    }

    def register(self, rel_type, rel_class):
        self.mapping[rel_type] = rel_class

    def unregister(self, rel_type):
        self.mapping.pop(rel_type, None)

    def from_json(self, related_class_name, var_name, rel_type, required=False):
        if not rel_type in self.mapping:
            msg = "No relation type available to handle '{0}'.".format(
                rel_type
            )
            raise NoSuchRelationError(msg)

        return self.mapping[rel_type](
            related_class_name,
            var_name,
            required=required
        )