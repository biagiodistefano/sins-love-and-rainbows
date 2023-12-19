from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from .shorturl_controller import ShortURLController
from .slr_controller import SLRController
from .twilio_controller import TwilioController

API_VERSION = "v0.0.2"

api = NinjaExtraAPI(
    title="Sins, Love and Rainbows API",
    version=API_VERSION,
    description=f"Party Management API {API_VERSION}",
    app_name=f"sinsloveandrainbows-api-{API_VERSION}",
    urls_namespace="slr-api",
    servers=[
        {"url": "https://sinsloveandrainbows.eu", "description": "Production Server"},
        # {"url": "http://localhost:8000", "description": "Development Server"},
    ]
)

api.register_controllers(
    NinjaJWTDefaultController,
    SLRController,
    ShortURLController,
    TwilioController,
)
