import boto3
from boto3.core.exceptions import NoSuchRelationError


class BaseRelation(object):
    is_relation = True

    def __init__(self, related_class_name, var_name, required=False):
        self.related_class = None
        self.parent_class = None

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
        pass

    def remove_from_instance(self):
        pass

    def proxy_to_class(self, *args, **kwargs):
        pass


class OneToOne(BaseRelation):
    is_one_to_one = True


class OneToMany(BaseRelation):
    is_one_to_many = True


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