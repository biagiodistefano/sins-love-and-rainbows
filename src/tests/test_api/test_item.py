import json

import pytest
from django.test.client import Client


@pytest.mark.django_db
def test_item(api_client: Client) -> None:
    # Create a test party
    create_party = api_client.post(
        "/api/party/create",
        data=json.dumps(
            {
                "name": "Test Party",
                "edition": "test-party",
                "date_and_time": "2021-08-17T18:00:00Z",
                "location": "Test Location",
                "description": "Test Description",
            }
        ),
        content_type="application/json",
    )
    assert create_party.status_code == 201
    party = create_party.json()
    party_edition = party["edition"]

    # Ensure there are no items initially
    assert party["item_set"] == []

    # Create an item
    create_item = api_client.post(
        f"/api/party/{party_edition}/item/create",
        data=json.dumps(
            {
                "category": "O",
                "name": "Test Item",
                "description": "Test Description",
                "quantity": "10",
                "url": "https://www.testitem.com",
            }
        ),
        content_type="application/json",
    )

    assert create_item.status_code == 201
    item = create_item.json()
    item_id = item["id"]

    # Read party and verify the item is associated
    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"]) == 1

    # Read the created item
    read_item = api_client.get(f"/api/party/{party_edition}/item/{item_id}")
    assert read_item.status_code == 200
    assert read_item.json() == item

    # Update the item
    update_item = api_client.put(
        f"/api/party/{party_edition}/item/{item_id}",
        data=json.dumps({"description": "Updated Description"}),
        content_type="application/json",
    )
    assert update_item.status_code == 200

    # Verify the item has been updated
    read_updated_item = api_client.get(f"/api/party/{party_edition}/item/{item_id}")
    assert read_updated_item.status_code == 200
    assert read_updated_item.json()["description"] == "Updated Description"

    # Create another item
    create_item2 = api_client.post(
        f"/api/party/{party_edition}/item/create",
        data=json.dumps(
            {
                "category": "D",
                "name": "Test Item 2",
                "description": "Test Description 2",
                "quantity": "5",
            }
        ),
        content_type="application/json",
    )
    assert create_item2.status_code == 201

    # List all items and verify count and names
    list_items = api_client.get(f"/api/party/{party_edition}/item/all")
    assert list_items.status_code == 200
    assert len(list_items.json()) == 2
    assert set(m["name"] for m in list_items.json()) == {"Test Item", "Test Item 2"}

    # Delete the first item
    delete_item = api_client.delete(f"/api/party/{party_edition}/item/{item_id}")
    assert delete_item.status_code == 204

    # Verify the deleted item is not accessible
    read_deleted_item = api_client.get(f"/api/party/{party_edition}/item/{item_id}")
    assert read_deleted_item.status_code == 404

    # List items again and verify the count and description of the remaining item
    list_items_after_delete = api_client.get(f"/api/party/{party_edition}/item/all")
    assert list_items_after_delete.status_code == 200
    assert len(list_items_after_delete.json()) == 1
    assert list_items_after_delete.json()[0]["description"] == "Test Description 2"

    # Delete all remaining items
    delete_all_items = api_client.delete(f"/api/party/{party_edition}/item/all")
    assert delete_all_items.status_code == 204

    # Verify no items remain
    list_items_empty = api_client.get(f"/api/party/{party_edition}/item/all")
    assert list_items_empty.status_code == 200
    assert len(list_items_empty.json()) == 0


@pytest.mark.django_db
def test_item_ingredients(api_client: Client) -> None:
    # Create a test party
    create_party = api_client.post(
        "/api/party/create",
        data=json.dumps(
            {
                "name": "Test Party",
                "edition": "test-party",
                "date_and_time": "2021-08-17T18:00:00Z",
                "location": "Test Location",
                "description": "Test Description",
            }
        ),
        content_type="application/json",
    )
    assert create_party.status_code == 201
    party = create_party.json()
    party_edition = party["edition"]

    # Create an item
    create_item = api_client.post(
        f"/api/party/{party_edition}/item/create",
        data=json.dumps(
            {
                "category": "O",
                "name": "Test Item",
                "description": "Test Description",
                "quantity": "10",
                "url": "https://www.testitem.com",
            }
        ),
        content_type="application/json",
    )
    assert create_item.status_code == 201
    item = create_item.json()
    item_id = item["id"]

    # Create an ingredient
    create_ingredient = api_client.post(
        "/api/ingredient/create",
        data=json.dumps(
            {
                "name": "Test Ingredient",
                "description": "Test Description",
            }
        ),
        content_type="application/json",
    )
    assert create_ingredient.status_code == 201
    ingredient = create_ingredient.json()
    ingredient_id = ingredient["id"]

    # Add the ingredient to the item
    add_ingredient = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/ingredient/{ingredient_id}/add",
    )
    assert add_ingredient.status_code == 400

    update_item = api_client.put(
        f"/api/party/{party_edition}/item/{item_id}",
        data=json.dumps({"category": "F"}),
        content_type="application/json",
    )
    assert update_item.status_code == 200

    add_ingredient = api_client.post(
        f"/api/party/{party_edition}/item/4/ingredient/7/add",
    )
    assert add_ingredient.status_code == 404

    # Add the ingredient to the item
    add_ingredient = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/ingredient/{ingredient_id}/add",
    )
    assert add_ingredient.status_code == 201

    # Remove the ingredient from the item
    remove_ingredient = api_client.delete(
        f"/api/party/{party_edition}/item/7/ingredient/7/remove",
    )
    assert remove_ingredient.status_code == 404

    # Remove the ingredient from the item
    remove_ingredient = api_client.delete(
        f"/api/party/{party_edition}/item/{item_id}/ingredient/{ingredient_id}/remove",
    )
    assert remove_ingredient.status_code == 204


@pytest.mark.django_db
def test_item_people(api_client: Client) -> None:
    create_person = api_client.post(
        "/api/person/create",
        data=json.dumps({"name": "John Doe", "from_abroad": False, "in_broadcast": True}),
        content_type="application/json",
    )
    assert create_person.status_code == 201
    person = create_person.json()
    person_id = person["id"]

    create_party = api_client.post(
        "/api/party/create",
        data=json.dumps(
            {
                "name": "Test Party",
                "edition": "test-party",
                "date_and_time": "2021-08-17T18:00:00Z",
                "location": "Test Location",
                "description": "Test Description",
            }
        ),
        content_type="application/json",
    )
    assert create_party.status_code == 201
    party = create_party.json()
    party_edition = party["edition"]

    person_2 = api_client.post(
        "/api/person/create",
        data=json.dumps({"name": "Jane Doe", "from_abroad": False, "in_broadcast": True}),
        content_type="application/json",
    )
    assert person_2.status_code == 201
    person_2 = person_2.json()
    person_2_id = person_2["id"]

    # Create an item
    create_item = api_client.post(
        f"/api/party/{party_edition}/item/create",
        data=json.dumps(
            {
                "category": "O",
                "name": "Test Item",
                "description": "Test Description",
                "quantity": "10",
                "url": "https://www.testitem.com",
            }
        ),
        content_type="application/json",
    )
    assert create_item.status_code == 201
    item = create_item.json()
    item_id = item["id"]

    # Add the person to the item
    add_person = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_id}/assign",
    )
    assert add_person.status_code == 201

    # Add the person to the item
    add_person = api_client.post(
        f"/api/party/{party_edition}/item/7/person/{person_id}/assign",
    )
    assert add_person.status_code == 404

    remove_person = api_client.delete(
        f"/api/party/{party_edition}/item/7/person/{person_id}/unassign",
    )
    assert remove_person.status_code == 404

    # Add the person to the item
    add_person_not_invited = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_2_id}/assign",
    )
    assert add_person_not_invited.status_code == 400
    assert "not invited" in add_person_not_invited.json()["message"]

    # Invite the person
    invite_person = api_client.post(
        f"/api/party/{party_edition}/invite/{person_2_id}/create",
    )
    assert invite_person.status_code == 201

    # Decline the invitation
    decline_invitation = api_client.put(
        f"/api/party/{party_edition}/invite/{person_2_id}/n",
    )
    assert decline_invitation.status_code == 200

    # Add the person to the item
    add_person_declined = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_2_id}/assign",
    )
    assert add_person_declined.status_code == 400
    assert "declined" in add_person_declined.json()["message"]

    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"]) == 1
    assert len(read_party.json()["item_set"][0]["assigned_to"]) == 1

    # Remove the person from the item
    remove_person = api_client.delete(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_id}/unassign",
    )
    assert remove_person.status_code == 204

    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"][0]["assigned_to"]) == 0

    # Add the person to the item
    add_person = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_id}/assign",
    )
    assert add_person.status_code == 201

    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"][0]["assigned_to"]) == 1

    # Remove all people from the item
    remove_all_people = api_client.delete(
        f"/api/party/{party_edition}/item/{item_id}/person/all",
    )
    assert remove_all_people.status_code == 204

    # Remove all people from the item
    remove_all_people = api_client.delete(
        f"/api/party/{party_edition}/item/7/person/all",
    )
    assert remove_all_people.status_code == 404

    # Verify no people remain
    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"][0]["assigned_to"]) == 0

    # Add the person to the item
    add_person = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_id}/assign",
    )
    assert add_person.status_code == 201

    # Uninvite the person
    uninvite_person = api_client.delete(
        f"/api/party/{party_edition}/invite/{person_id}",
    )
    assert uninvite_person.status_code == 204

    # Verify no people remain
    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"][0]["assigned_to"]) == 0

    # Re invite the person
    invite_person = api_client.post(
        f"/api/party/{party_edition}/invite/{person_id}/create",
    )
    assert invite_person.status_code == 201

    # Add the person to the item
    add_person = api_client.post(
        f"/api/party/{party_edition}/item/{item_id}/person/{person_id}/assign",
    )
    assert add_person.status_code == 201

    # The person declines the invite
    decline_invitation = api_client.put(
        f"/api/party/{party_edition}/invite/{person_id}/n",
    )
    assert decline_invitation.status_code == 200

    # Verify no people remain
    read_party = api_client.get(f"/api/party/{party_edition}")
    assert read_party.status_code == 200
    assert len(read_party.json()["item_set"][0]["assigned_to"]) == 0
