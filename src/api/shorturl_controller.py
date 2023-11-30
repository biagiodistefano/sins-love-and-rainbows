import typing as t

from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404
from ninja.constants import NOT_SET
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from . import models, schema, settings

AUTH = JWTAuth() if settings.USE_AUTH else NOT_SET


@api_controller(prefix_or_class="/s", tags=["Short URL"], auth=JWTAuth())
class ShortURLController:  # type: ignore

    @route.post("/create", response={201: schema.ShortURLSchema})
    def create_short_url(self, request: HttpRequest, url: schema.ShortURLSchemaCreate):
        short_url = models.ShortUrl.objects.create(**url.dict(exclude_none=True))
        return 201, short_url

    @route.get("/{short_url}", response=schema.ShortURLSchema)
    def get_short_url(self, request: HttpRequest, short_url: str):
        short_url = get_object_or_404(models.ShortUrl, short_url=short_url)
        return short_url

    @route.get("/", response=t.List[schema.ShortURLSchema])
    def get_short_urls(self, request: HttpRequest):
        return models.ShortUrl.objects.all()

    @route.put("/{short_url}", response=schema.ShortURLSchema)
    def update_short_url(self, request: HttpRequest, short_url: str, url: schema.ShortURLSchemaCreate):
        instance = get_object_or_404(models.ShortUrl, short_url=short_url)
        for k, v in url.dict(exclude_none=True).items():
            setattr(instance, k, v)
        instance.save()
        return instance

    @route.delete("/{short_url}", response={204: None})
    def delete_short_url(self, request: HttpRequest, short_url: str):
        models.ShortUrl.objects.filter(short_url=short_url).delete()
        return 204, None
