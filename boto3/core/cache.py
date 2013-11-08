from boto3.core.exceptions import NotCached


class ServiceCache(object):
    """
    A centralized registry of classes that have already been built.

    Present to both prevent too much factory churn as well as to give the
    resource layer something to refer to in relations.
    """
    # TODO: We may want to add LRU/expiration behavior in the future, to
    #       prevent the cache from taking up too much space.
    #       Unlikely, but potential.
    def __init__(self):
        self.services = {}

    def get_connection(self, service_name):
        service = self.services.get(service_name, {})
        connection_class = service.get('connection', None)

        if not connection_class:
            msg = "Connection for '{0}' is not present in the cache."
            raise NotCached(msg.format(
                service_name
            ))

        return connection_class

    def set_connection(self, service_name, to_cache):
        self.services.setdefault(service_name, {})
        self.services[service_name]['connection'] = to_cache

    def del_connection(self, service_name):
        # Unlike ``get_connection``, this should be fire & forget.
        # We don't really care, as long as it's not in the cache any longer.
        try:
            del self.services[service_name]['connection']
        except KeyError:
            pass

    def get_resource(self, service_name, resource_name):
        service = self.services.get(service_name, {})
        resources = service.get('resources', {})
        resource_class = resources.get(resource_name, None)

        if not resource_class:
            msg = "Resource '{0}' for {1} is not present in the cache."
            raise NotCached(msg.format(
                resource_name,
                service_name
            ))

        return resource_class

    def set_resource(self, service_name, resource_name, to_cache):
        self.services.setdefault(service_name, {})
        self.services[service_name].setdefault('resources', {})
        self.services[service_name]['resources'][resource_name] = to_cache

    def del_resource(self, service_name, resource_name):
         # Unlike ``get_resource``, this should be fire & forget.
        # We don't really care, as long as it's not in the cache any longer.
        try:
            del self.services[service_name]['resources'][resource_name]
        except KeyError:
            pass

    def get_collection(self, service_name, collection_name):
        service = self.services.get(service_name, {})
        collections = service.get('collections', {})
        collection_class = collections.get(collection_name, None)

        if not collection_class:
            msg = "Collection '{0}' for {1} is not present in the cache."
            raise NotCached(msg.format(
                collection_name,
                service_name
            ))

        return collection_class

    def set_collection(self, service_name, collection_name, to_cache):
        self.services.setdefault(service_name, {})
        self.services[service_name].setdefault('collections', {})
        self.services[service_name]['collections'][collection_name] = to_cache

    def del_collection(self, service_name, collection_name):
         # Unlike ``get_collection``, this should be fire & forget.
        # We don't really care, as long as it's not in the cache any longer.
        try:
            del self.services[service_name]['collections'][collection_name]
        except KeyError:
            pass
