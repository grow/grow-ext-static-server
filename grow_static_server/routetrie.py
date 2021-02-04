class RouteTrie(object):
    """Trie data struct for efficient URL lookups."""

    def __init__(self):
        self.children = {}
        self.param_child = None
        self.wildcard_child = None
        self.value = None
        self.permanent = False

    def add(self, route, value, permanent=False):
        route = self._normalize_route(route)

        # If the end was reached, save the value to the node.
        if route == '':
            self.value = value
            self.permanent = permanent
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
        next_node.add(tail, value, permanent=permanent)

    def get(self, route):
        params = {}
        value, permanent = self._get_value(route, params)
        return value, params, permanent

    def _get_value(self, route, params):
        route = self._normalize_route(route)
        if route == '':
            return self.value, self.permanent

        head, tail = self._split_route(route)

        # Check for direct matches.
        child = self.children.get(head)
        if child:
            value, permanent = child._get_value(tail, params)
            if value is not None:
                return value, permanent

        if self.param_child:
            value, permanent = self.param_child.trie._get_value(tail, params)
            if value is not None:
                params[self.param_child.name] = head
                return value, permanent

        if self.wildcard_child:
            params[self.wildcard_child.name] = route
            return self.wildcard_child.value, self.wildcard_child.permanent

        return None, None

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
    def __init__(self, name, value, permanent=False):
        self.name = name
        self.value = value
        self.permanent = permanent
