from datetime import datetime

from ninja.schema import Schema
from pydantic import Field, UUID4, field_validator


class PersonSchemaCreate(Schema):
    name: str = Field(..., min_length=2, max_length=30)
    from_abroad: bool
    in_broadcast: bool


class PersonSchemaUpdate(Schema):
    name: str | None = Field(None, min_length=2, max_length=30)
    from_abroad: bool | None
    in_broadcast: bool | None


class PersonSchema(PersonSchemaCreate):
    id: UUID4


class InviteSchema(Schema):
    person: PersonSchema
    status: str = Field(..., min_length=1, max_length=1, pattern="^[YMN]$")
    last_updated: datetime
    party_edition: str = Field(..., min_length=1, max_length=30)


class IngredientSchemaCreate(Schema):
    name: str = Field(..., min_length=2, max_length=30)

    @field_validator("name")
    def validate_lowercase(cls, value: str) -> str:
        return value.lower()


class IngredientSchema(IngredientSchemaCreate):
    id: int


class AllergySchema(Schema):
    ingredient: IngredientSchema
    people: list[PersonSchema]


class InviteSummarySchema(Schema):
    yes: int
    maybe: int
    no: int
    from_abroad: int


class InviteListSchema(Schema):
    yes: list[InviteSchema]
    maybe: list[InviteSchema]
    no: list[InviteSchema]


class ExternalLinkSchemaCreate(Schema):
    name: str = Field(..., min_length=2, max_length=30)
    url: str
    description: str | None = Field(None, min_length=2, max_length=250)


class ExternalLinkSchema(ExternalLinkSchemaCreate):
    id: int
    party_edition: str = Field(..., min_length=1, max_length=30)


class ExternalLinkSchemaUpdate(Schema):
    name: str | None = Field(None, min_length=2, max_length=30)
    url: str | None
    description: str | None = Field(None, min_length=2, max_length=250)


class MessageSchemaCreate(Schema):
    text: str = Field(..., min_length=2, max_length=250)


class MessageSchema(MessageSchemaCreate):
    id: int
    party_edition: str
    text_rendered: str
    sent_at: datetime | None
    sent_stats: str | None


class ItemSchemaCreate(Schema):
    category: str = Field(..., min_length=1, max_length=1, pattern="^[FDO]$")
    name: str = Field(..., min_length=2, max_length=120)
    description: str | None = Field(None, min_length=2, max_length=250)
    quantity: str | None = Field(None, min_length=1, max_length=30)
    url: str | None


class ItemSchemaUpdate(ItemSchemaCreate):
    category: str | None = Field(None, min_length=1, max_length=1, pattern="^[FDO]$")
    name: str | None = Field(None, min_length=2, max_length=120)


class ItemSchema(Schema):
    id: int
    party_edition: str
    category: str
    name: str
    description: str | None
    quantity: str | None
    url: str | None
    ingredients: list[IngredientSchema]
    assigned_to: list[PersonSchema]
    # allergens: list[str]
    allergic_people: list[PersonSchema]


class PartySchemaCreate(Schema):
    name: str = Field(..., min_length=2, max_length=30)
    edition: str = Field(..., min_length=1, max_length=30)
    date_and_time: datetime
    location: str | None = Field(None, min_length=2, max_length=120)
    description: str | None

    @field_validator("edition")
    def validate_lowercase(cls, value: str) -> str:
        return value.lower()


class PartySchemaUpdate(PartySchemaCreate):
    name: str | None = Field(None, min_length=2, max_length=30)
    edition: str | None = Field(None, min_length=2, max_length=30)
    date_and_time: datetime | None
    location: str | None = Field(None, min_length=2, max_length=120)
    description: str | None

    @field_validator("edition")
    def validate_lowercase(cls, value: str) -> str:
        return value.lower()


class PartySchema(PartySchemaCreate):
    logo_url: str | None
    description_rendered: str | None
    invite_summary: InviteSummarySchema
    invite_set: list[InviteSchema]
    not_invited_people: list[PersonSchema]
    allergy_list: list[str]
    externallink_set: list[ExternalLinkSchema]
    message_set: list[MessageSchema]
    item_set: list[ItemSchema]


class PartyPreviewSchema(PartySchemaCreate):
    name: str = Field(..., min_length=2, max_length=30)
    edition: str = Field(..., min_length=1, max_length=30)
    date_and_time: datetime
    location: str | None = Field(None, min_length=2, max_length=120)
    logo_url: str | None
    description_rendered: str | None
    invite_summary: InviteSummarySchema


class ShortURLSchemaCreate(Schema):
    url: str
    short_url: str = Field(None, max_length=16)


class ShortURLSchema(ShortURLSchemaCreate):
    id: int
    created_at: datetime
    updated_at: datetime
