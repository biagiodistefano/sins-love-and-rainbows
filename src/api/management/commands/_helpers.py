from datetime import datetime

from api.models import Allergy, Ingredient, Item, Party, Person
from wasabi import msg


def load_people(filename: str) -> None:
    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            p, created = Person.objects.get_or_create(name=line.strip())
            if created:
                msg.good(f"Loaded {p}")
            else:
                msg.warn(f"Skipped {p} (already exists)")


def load_allergies(filename: str) -> None:
    with open(filename) as f:
        for line in f:
            if not line.strip():
                continue
            ingredient, *people = line.split(",")
            ingredient = ingredient.strip()
            people = [p.strip() for p in people if p.strip()]
            i, created = Ingredient.objects.get_or_create(name=ingredient)
            if created:
                msg.good(f"Created ingredient {i!r}")
            for person in people:
                p, created = Person.objects.get_or_create(name=person)
                if created:
                    msg.good(f"Created person {p!r}")
                a, created = Allergy.objects.get_or_create(ingredient=i)
                if created:
                    msg.good(f"Created allergy {a!r}")
                a.people.add(p)
                msg.good(f"Added {p!r} to {a!r}")


def create_test_party() -> Party:
    load_people("people.txt")
    load_allergies("allergies.txt")

    party, _ = Party.objects.get_or_create(
        name="Test Party", edition="Test Edition", date_and_time=datetime(2020, 1, 1, 12, 0, 0)
    )  # noqa: E501

    caponata = _create_caponata(party)
    party.item_set.add(caponata)
    biagio, _ = Person.objects.get_or_create(name="Biagio")
    party.invite(biagio)
    caponata.assign_to(biagio)

    beer = Item.objects.create(name="Beer", party=party, category="D")
    party.item_set.add(beer)
    kate, _ = Person.objects.get_or_create(name="Kate")
    party.invite(kate)
    beer.assign_to(kate)

    party.save()
    return party


def _create_caponata(party: Party) -> Item:
    caponata, _ = Item.objects.get_or_create(name="Caponata", party=party, category="F")
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="eggplant")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="tomato")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="onion")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="celery")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="olive oil")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="vinegar")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="sugar")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="salt")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="pepper")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="capers")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="olives")[0])
    caponata.ingredients.add(Ingredient.objects.get_or_create(name="nuts")[0])
    return caponata
