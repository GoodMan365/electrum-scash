"""Lightning router stub for Scash."""

class LNPathFinder:
    def __init__(self, *args, **kwargs):
        pass

class NodeInfo:
    def __init__(self, *args, **kwargs):
        pass

class PathEdge:
    def __init__(self, *args, **kwargs):
        pass

class RouteEdge:
    def __init__(self, *args, **kwargs):
        pass

class TrampolineEdge:
    def __init__(self, *args, **kwargs):
        pass

class LNPaymentTRoute:
    def __init__(self, *args, **kwargs):
        pass

def is_route_within_budget(*args, **kwargs):
    return False

__all__ = [
    'LNPathFinder', 'NodeInfo', 'PathEdge', 'RouteEdge',
    'TrampolineEdge', 'LNPaymentTRoute', 'is_route_within_budget'
]
