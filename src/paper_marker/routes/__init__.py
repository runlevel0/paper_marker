from paper_marker.routes.marker_route import MarkerRoute
from paper_marker.routes.markitdown_route import MarkItDownRoute
from paper_marker.routes.mineru_route import MinerURoute
from paper_marker.routes.nougat_route import NougatRoute

ROUTE_REGISTRY = {
    MarkerRoute.name: MarkerRoute,
    MinerURoute.name: MinerURoute,
    NougatRoute.name: NougatRoute,
    MarkItDownRoute.name: MarkItDownRoute,
}

DEFAULT_ROUTES = [MarkerRoute.name, MinerURoute.name, NougatRoute.name, MarkItDownRoute.name]
