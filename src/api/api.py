from ninja_extra import NinjaExtraAPI

from .slr_controller import SLRController
from .shorturl_controller import ShortURLController
from ninja_jwt.controller import NinjaJWTDefaultController


API_VERSION = "v0.0.1"

api = NinjaExtraAPI(
    title="Sins, Love and Rainbows API",
    version=API_VERSION,
    description=f"Party Management API {API_VERSION}",
    app_name=f"sinsloveandrainbows-api-{API_VERSION}",
    urls_namespace="slr-api",
    servers=[
        {"url": "http://localhost:8000", "description": "Development Server"},
        {"url": "https://www.sinsloveandrainbows.eu", "description": "Production Server"}
    ]
)


api.register_controllers(
    NinjaJWTDefaultController,
    SLRController,
    ShortURLController,
)
