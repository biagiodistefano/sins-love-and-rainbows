import typing as t

from django.db import transaction
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, Http404
from ninja import File
from ninja.constants import NOT_SET
from ninja.files import UploadedFile
from ninja.schema import Schema
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from . import models
from . import schema
from . import settings

AUTH = JWTAuth() if settings.USE_AUTH else NOT_SET


@api_controller(tags=["Sins, Love and Rainbows"], auth=AUTH)
class SLRController:  # type: ignore

    # Party

    @route.post("/party/create", tags=["party"], response={201: schema.PartySchema})
    def create_party(self, request: HttpRequest, party: schema.PartySchemaCreate):
        return 201, models.Party.objects.create(**party.dict())

    @route.post("/party/{edition}/logo", tags=["party"], response={200: schema.PartySchema})
    def upload_logo(self, request: HttpRequest, edition: str, file: UploadedFile = File(...)):
        party = get_object_or_404(models.Party, edition=edition)
        party.logo = file
        party.save()
        return 200, party

    @route.get("/party/all", tags=["party"], response={200: list[schema.PartyPreviewSchema]})
    def list_parties(self, request: HttpRequest):
        return 200, list(models.Party.objects.all())

    @route.get("/party/{edition}", tags=["party"], response={200: schema.PartySchema})
    def read_party(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, party

    @route.put("/party/{edition}", tags=["party"], response={200: schema.PartySchema})
    def update_party(self, request: HttpRequest, edition: str, party: schema.PartySchemaUpdate):
        return 200, self.update_object(models.Party, party, edition=edition)

    @route.delete("/party/{edition}", tags=["party"], response={204: None})
    def delete_party(self, request: HttpRequest, edition: str):
        models.Party.objects.filter(edition=edition).delete()
        return 204, None

    @route.post("/party/{edition}/message/create", tags=["party"], response={201: schema.MessageSchema})
    def create_message(self, request: HttpRequest, edition: str, message: schema.MessageSchemaCreate):
        party = get_object_or_404(models.Party, edition=edition)
        message = models.Message.objects.create(party=party, **message.dict(exclude_none=True))
        return 201, message

    @route.get("/party/{edition}/message/all", tags=["party"], response={200: list[schema.MessageSchema]})
    def list_messages(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, party.message_set.all()

    @route.get("/party/{edition}/message/{message_id}", tags=["party"], response={200: schema.MessageSchema})
    def read_message(self, request: HttpRequest, edition: str, message_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        if message := party.message_set.filter(id=message_id).first():
            return 200, message
        raise Http404

    @route.put("/party/{edition}/message/{message_id}", tags=["party"], response={200: schema.MessageSchema})
    def update_message(self, request: HttpRequest, edition: str, message_id: int, message: schema.MessageSchemaCreate):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, self.update_object(party.message_set, message, id=message_id)

    @route.delete("/party/{edition}/message/{message_id}", tags=["party"], response={204: None})
    def delete_message(self, request: HttpRequest, edition: str, message_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        party.message_set.filter(id=message_id).delete()
        return 204, None

    # send a message to all people who are invited to the party
    @route.post("/party/{edition}/message/{message_id}/send", tags=["party"], response={202: schema.MessageSchema})
    def send_message(self, request: HttpRequest, edition: str, message_id: int, include_declined: bool = True):
        party = get_object_or_404(models.Party, edition=edition)
        if message := party.message_set.filter(id=message_id).first():
            message.send(include_declined=include_declined)
            return 202, message
        raise Http404

    @route.delete("/party/{edition}/message/all", tags=["party"], response={204: None})
    def delete_all_messages(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        party.message_set.all().delete()
        return 204, None

    @route.get("/party/{edition}/invite/all", tags=["party", "invites"], response={200: list[schema.InviteSchema]})
    def list_invites(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, list(party.invite_set.all())

    @route.get("/party/{edition}/not-invited/all", tags=["party", "invites"], response={200: list[schema.PersonSchema]})
    def list_not_invited_people(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, party.not_invited_people()

    @route.post("/party/{edition}/invite/{person_id}/create", tags=["party", "invites"],
                response={201: schema.InviteSchema}, url_name="invite_person")
    def invite_person(self, request: HttpRequest, edition: str, person_id: str):
        party = get_object_or_404(models.Party, edition=edition)
        person = get_object_or_404(models.Person, id=person_id)
        return 201, models.Invite.objects.get_or_create(party=party, person=person)[0]

    @route.delete("/party/{edition}/invite/{person_id}", tags=["party", "invites"], response={204: None}, url_name="uninvite_person")
    def uninvite_person(self, request: HttpRequest, edition: str, person_id: str):
        party = get_object_or_404(models.Party, edition=edition)
        person = get_object_or_404(models.Person, id=person_id)
        models.Invite.objects.filter(party=party, person=person).delete()
        items = party.item_set.filter(assigned_to=person)
        for item in items:
            item.assigned_to.remove(person)
        return 204, None

    @route.put("/party/{edition}/invite/{person_id}/{status}", tags=["party", "invites"],
               response={200: schema.InviteSchema}, url_name="update_invite_status")
    def update_invite(self, request: HttpRequest, edition: str, person_id: str, status: t.Literal["y", "m", "n"]):
        party = get_object_or_404(models.Party, edition=edition)
        person = get_object_or_404(models.Person, id=person_id)
        invite = models.Invite.objects.get_or_create(party=party, person=person)[0]
        invite.status = status.upper()
        with transaction.atomic():
            if invite.status == "N":
                items = party.item_set.filter(assigned_to=person)
                for item in items:
                    item.assigned_to.remove(person)
            invite.save()
        return 200, invite

    @route.post("/party/{edition}/external-link/create", tags=["party", "external_links"],
                response={201: schema.ExternalLinkSchema})
    def create_external_link(self, request: HttpRequest, edition: str, external_link: schema.ExternalLinkSchemaCreate):
        party = get_object_or_404(models.Party, edition=edition)
        return 201, models.ExternalLink.objects.create(party=party, **external_link.dict())

    @route.get("/party/{edition}/external-link/all", tags=["party", "external_links"],
               response={200: list[schema.ExternalLinkSchema]})
    def list_external_links(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, list(party.externallink_set.all())

    @route.get("/party/{edition}/external-link/{external_link_id}", tags=["party", "external_links"],
               response={200: schema.ExternalLinkSchema})
    def read_external_link(self, request: HttpRequest, edition: str, external_link_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        if external_link := party.externallink_set.filter(id=external_link_id).first():
            return 200, external_link
        raise Http404

    @route.put("/party/{edition}/external-link/{external_link_id}", tags=["party", "external_links"],
               response={200: schema.ExternalLinkSchema})
    def update_external_link(self, request: HttpRequest, edition: str, external_link_id: int,
                             external_link: schema.ExternalLinkSchemaUpdate):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, self.update_object(party.externallink_set, external_link, id=external_link_id)

    @route.delete("/party/{edition}/external-link/all", tags=["party", "external_links"], response={204: None})
    def delete_all_external_links(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        party.externallink_set.all().delete()
        return 204, None

    @route.delete("/party/{edition}/external-link/{external_link_id}", tags=["party", "external_links"],
                  response={204: None})
    def delete_external_link(self, request: HttpRequest, edition: str, external_link_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        party.externallink_set.filter(id=external_link_id).delete()
        return 204, None

    # People

    @route.post("/person/create", tags=["people"], response={201: schema.PersonSchema}, url_name="create_person")
    def create_person(self, request: HttpRequest, person: schema.PersonSchemaCreate):
        return 201, models.Person.objects.create(**person.dict())

    @route.get("/person/{person_id}", tags=["people"], response={200: schema.PersonSchema})
    def read_person(self, request: HttpRequest, person_id: str):
        return 200, get_object_or_404(models.Person, id=person_id)

    @route.put("/person/{person_id}", tags=["people"], response={200: schema.PersonSchema})
    def update_person(self, request: HttpRequest, person_id: str, person: schema.PersonSchemaUpdate):
        return 200, self.update_object(models.Person, person, id=person_id)

    @route.delete("/person/{person_id}", tags=["people"], response={204: None})
    def delete_person(self, request: HttpRequest, person_id: str):
        models.Person.objects.filter(id=person_id).delete()
        return 204, None

    # Ingredients

    @route.post("/ingredient/create", tags=["ingredients"], response={201: schema.IngredientSchema})
    def create_ingredient(self, request: HttpRequest, ingredient: schema.IngredientSchemaCreate):
        return 201, models.Ingredient.objects.create(**ingredient.dict())

    @route.get("/ingredient/all", tags=["ingredients"], response={200: list[schema.IngredientSchema]})
    def list_ingredients(self, request: HttpRequest):
        return 200, list(models.Ingredient.objects.all())

    @route.get("/ingredient/{ingredient_id}", tags=["ingredients"], response={200: schema.IngredientSchema})
    def read_ingredient(self, request: HttpRequest, ingredient_id: str):
        return 200, get_object_or_404(models.Ingredient, id=ingredient_id)

    @route.put("/ingredient/{ingredient_id}", tags=["ingredients"], response={200: schema.IngredientSchema})
    def update_ingredient(self, request: HttpRequest, ingredient_id: str, ingredient: schema.IngredientSchemaCreate):
        return 200, self.update_object(models.Ingredient, ingredient, id=ingredient_id)

    @route.delete("/ingredient/{ingredient_id}", tags=["ingredients"], response={204: None})
    def delete_ingredient(self, request: HttpRequest, ingredient_id: str):
        models.Ingredient.objects.filter(id=ingredient_id).delete()
        return 204, None

    @route.post("/ingredient/{ingredient_id}/allergy/{person_id}/create", tags=["ingredients", "allergies"],
                response={201: schema.AllergySchema})
    def create_allergy(self, request: HttpRequest, ingredient_id: str, person_id: str):
        ingredient = get_object_or_404(models.Ingredient, id=ingredient_id)
        person = get_object_or_404(models.Person, id=person_id)
        allergy = models.Allergy.objects.get_or_create(ingredient=ingredient)[0]
        allergy.people.add(person)
        return 201, allergy

    @route.get("/ingredient/{ingredient_id}/allergy", tags=["ingredients", "allergies"],
               response={200: schema.AllergySchema, 404: None})
    def read_allergy(self, request: HttpRequest, ingredient_id: str):
        ingredient = get_object_or_404(models.Ingredient, id=ingredient_id)
        try:
            return 200, ingredient.allergy
        except models.Ingredient.allergy.RelatedObjectDoesNotExist:
            return 404, None

    @route.get("/person/{person_id}/allergies", tags=["people", "allergies"],
               response={200: t.List[schema.IngredientSchema]})
    def list_person_allergies(self, request: HttpRequest, person_id: str):
        person = get_object_or_404(models.Person, id=person_id)
        return 200, [allergy.ingredient for allergy in person.allergy_set.all().select_related("ingredient")]

    @route.delete("/ingredient/{ingredient_id}/allergy/{person_id}", tags=["ingredients", "allergies"],
                  response={204: None})
    def delete_allergy(self, request: HttpRequest, ingredient_id: str, person_id: str):
        allergy = get_object_or_404(models.Allergy, ingredient_id=ingredient_id)
        person = get_object_or_404(models.Person, id=person_id)
        allergy.people.remove(person)
        return 204, None

    @route.post("/party/{edition}/item/create", tags=["party", "items"], response={201: schema.ItemSchema})
    def create_item(self, request: HttpRequest, edition: str, item: schema.ItemSchemaCreate):
        party = get_object_or_404(models.Party, edition=edition)
        return 201, models.Item.objects.create(party=party, **item.dict(exclude_none=True))

    @route.get("/party/{edition}/item/all", tags=["party", "items"], response={200: list[schema.ItemSchema]})
    def list_items(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, list(party.item_set.all())

    @route.get("/party/{edition}/item/{item_id}", tags=["party", "items"], response={200: schema.ItemSchema})
    def read_item(self, request: HttpRequest, edition: str, item_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        if item := party.item_set.filter(id=item_id).first():
            return 200, item
        raise Http404

    @route.put("/party/{edition}/item/{item_id}", tags=["party", "items"], response={200: schema.ItemSchema})
    def update_item(self, request: HttpRequest, edition: str, item_id: int, item: schema.ItemSchemaUpdate):
        party = get_object_or_404(models.Party, edition=edition)
        return 200, self.update_object(party.item_set, item, id=item_id)

    @route.post("/party/{edition}/item/{item_id}/ingredient/{ingredient_id}/add",
                tags=["party", "items", "ingredients"], response={201: schema.ItemSchema, 400: dict[str, str]})
    def add_ingredient_to_item(self, request: HttpRequest, edition: str, item_id: int, ingredient_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        item = party.item_set.filter(id=item_id).first()
        if item is None:
            raise Http404
        if item.category not in ("F", "D"):
            return 400, {"message": "Only food and drink items can have ingredients"}
        ingredient = get_object_or_404(models.Ingredient, id=ingredient_id)
        item.ingredients.add(ingredient)
        return 201, item

    @route.delete("/party/{edition}/item/{item_id}/ingredient/{ingredient_id}/remove",
                  tags=["party", "items", "ingredients"], response={204: None, 404: None})
    def remove_ingredient_from_item(self, request: HttpRequest, edition: str, item_id: int, ingredient_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        item = party.item_set.filter(id=item_id).first()
        if item is None:
            raise Http404
        ingredient = get_object_or_404(models.Ingredient, id=ingredient_id)
        item.ingredients.remove(ingredient)
        return 204, None

    @route.delete("/party/{edition}/item/all", tags=["party", "items"], response={204: None})
    def delete_all_items(self, request: HttpRequest, edition: str):
        party = get_object_or_404(models.Party, edition=edition)
        party.item_set.all().delete()
        return 204, None

    @route.delete("/party/{edition}/item/{item_id}", tags=["party", "items"], response={204: None})
    def delete_item(self, request: HttpRequest, edition: str, item_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        party.item_set.filter(id=item_id).delete()
        return 204, None

    @route.post("/party/{edition}/item/{item_id}/person/{person_id}/assign", tags=["party", "items", "people"],
                response={201: schema.ItemSchema, 400: dict[str, str]})
    def assign_person_to_item(self, request: HttpRequest, edition: str, item_id: int, person_id: str):
        party = get_object_or_404(models.Party, edition=edition)
        item = party.item_set.filter(id=item_id).first()
        if item is None:
            raise Http404
        person = get_object_or_404(models.Person, id=person_id)
        invite = party.invite_set.filter(person=person).first()
        if invite is None:
            return 400, {"message": f"{person.name} is not invited to this party"}
        if invite.status == "N":
            return 400, {"message": f"{person.name} has declined the invitation"}
        item.assigned_to.add(person)
        return 201, item

    @route.delete("/party/{edition}/item/{item_id}/person/{person_id}/unassign", tags=["party", "items", "people"],
                  response={204: None, 404: None})
    def unassign_person_from_item(self, request: HttpRequest, edition: str, item_id: int, person_id: str):
        party = get_object_or_404(models.Party, edition=edition)
        item = party.item_set.filter(id=item_id).first()
        if item is None:
            raise Http404
        person = get_object_or_404(models.Person, id=person_id)
        item.assigned_to.remove(person)
        return 204, None

    @route.delete("/party/{edition}/item/{item_id}/person/all", tags=["party", "items", "people"], response={204: None})
    def unassign_all_people_from_item(self, request: HttpRequest, edition: str, item_id: int):
        party = get_object_or_404(models.Party, edition=edition)
        item = party.item_set.filter(id=item_id).first()
        if item is None:
            raise Http404
        item.assigned_to.clear()
        return 204, None

    @staticmethod
    def update_object(model: t.Type[models.models.Model], data: Schema, **kwargs) -> models.models.Model:
        instance = get_object_or_404(model, **kwargs)
        for key, value in data.dict(exclude_none=True).items():
            setattr(instance, key, value)
        instance.save()
        return instance
