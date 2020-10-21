class RouteTrie(object):
    """Trie data struct for efficient URL lookups."""

    def __init__(self):
        self.children = {}
        self.param_child = None
        self.wildcard_child = None
        self.value = None

    def add(self, route, value):
        route = self._normalize_route(route)

        # If the end was reached, save the value to the node.
        if route == '':
            self.value = value
            return

        head, tail = self._split_route(route)

        if head[0] == '*':
            self.wildcard_child = WildcardChild(head, value)
            return

        next_node = None
        if head[0] == ':':
            if self.param_child is None:
                self.param_child = ParamChild(head)
            next_node = self.param_child.trie
        else:
            next_node = self.children.get(head)
            if next_node is None:
                next_node = RouteTrie()
                self.children[head] = next_node
        next_node.add(tail, value)

    def get(self, route):
        params = {}
        value = self._get_value(route, params)
        return value, params

    def _get_value(self, route, params):
        route = self._normalize_route(route)
        if route == '':
            return self.value

        head, tail = self._split_route(route)

        # Check for direct matches.
        child = self.children.get(head)
        if child:
            value = child._get_value(tail, params)
            if value is not None:
                return value

        if self.param_child:
            value = self.param_child.trie._get_value(tail, params)
            if value is not None:
                params[self.param_child.name] = head
                return value

        if self.wildcard_child:
            params[self.wildcard_child.name] = route
            return self.wildcard_child.value

        return None

    def _normalize_route(self, route):
        # Remove leading slashes.
        return route.lstrip('/')

    def _split_route(self, route):
        i = route.find('/')
        if i == -1:
            return route, ''
        return route[:i], route[i+1:]


class ParamChild(object):
    def __init__(self, name):
        self.name = name
        self.trie = RouteTrie()


class WildcardChild(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
