from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core import exceptions
from django.db import transaction
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template import loader
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from api import models
from . import notifications
from .forms import ItemForm, RsvpForm


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "slrportal/index.html", {"user": request.user})


def redirect_url(request: HttpRequest, short_url: str):
    instance = get_object_or_404(models.ShortUrl, short_url=short_url)
    return redirect(instance.url)


def get_next_party(request: HttpRequest) -> HttpResponse:
    upcoming_parties = models.Party.objects.filter(date_and_time__gte=timezone.now(), closed=False).order_by(
        "date_and_time"
    )

    for party in upcoming_parties:
        # If the party is not private, redirect to it
        if not party.private:
            return redirect_to_party(party)

        # If the party is private, check if the user is invited
        if request.user.is_authenticated:
            if models.Invite.objects.filter(party=party, person=request.user).first():
                return redirect_to_party(party)

    # If no suitable party is found
    raise Http404("No upcoming parties found or not invited to any.")


def redirect_to_party(party: models.Party) -> HttpResponse:
    url = reverse("party", kwargs={"edition": party.edition})
    return redirect(url)


def party_detail(request: HttpRequest, edition: str) -> HttpResponse:
    party = get_object_or_404(models.Party, edition=edition)
    invite = None
    if request.user.is_authenticated:
        invite = models.Invite.objects.filter(party=party, person=request.user).first()
    if party.private and invite is None:
        raise Http404("No upcoming parties found.")
    context = {"party": party, "person": request.user, "invite": invite}
    return render(request, "slrportal/party_detail.html", context)


@login_required
@require_POST
def claim_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    task = get_object_or_404(models.Item, id=item_id)
    person = get_object_or_404(models.Person, id=person_id)
    if request.user != person and not request.user.is_superuser:
        return HttpResponseBadRequest("You can only assign items to yourself")
    invite = models.Invite.objects.filter(party=task.party, person=person).first()
    if invite.party.closed:
        return HttpResponseBadRequest("Party is closed")
    if invite is None:
        return HttpResponseBadRequest("Not invited")
    if invite.status == "N":
        return HttpResponseBadRequest("Not attending")
    task.assigned_to.add(person)
    task.save()
    notifications.notify_admins_of_item_change.delay(task, person, "claimed")
    url = reverse("party", kwargs={"edition": task.party.edition})
    return redirect(url)


@login_required
@require_POST
def unclaim_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    task = get_object_or_404(models.Item, id=item_id)
    if task.party.closed:
        return HttpResponseBadRequest("Party is closed")
    person = get_object_or_404(models.Person, id=person_id)
    if request.user != person and not request.user.is_superuser:
        return HttpResponseBadRequest("You can only unassign items from yourself")
    task.assigned_to.remove(person)
    task.save()
    notifications.notify_admins_of_item_change.delay(task, person, "unclaimed")
    url = reverse("party", kwargs={"edition": task.party.edition})
    return redirect(url)


@login_required
@require_POST
def create_item(request: HttpRequest, edition: str) -> HttpResponse:
    party = get_object_or_404(models.Party, edition=edition)
    if party.closed:
        return HttpResponseBadRequest("Party is closed")
    form = ItemForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Invalid form: {}".format(form.errors))
    item = form.save(commit=False)
    item.party = party
    item.save()
    person_id = form.cleaned_data["person_id"]
    person = get_object_or_404(models.Person, id=person_id)
    invite = models.Invite.objects.filter(party=party, person=person).first()
    if invite is None:
        return HttpResponseBadRequest("Not invited")
    if invite.status == "N":
        return HttpResponseBadRequest("Not attending")
    url = reverse("party", kwargs={"edition": party.edition})
    action = "created"
    if form.cleaned_data["claim"]:
        item.assigned_to.add(form.cleaned_data["person_id"])
        action += " and claimed"
    item.created_by = person
    item.save()
    notifications.notify_admins_of_item_change.delay(item, person, action)
    return redirect(url)


@login_required
@require_POST
def delete_item(request: HttpRequest, item_id: str) -> HttpResponse:
    item = get_object_or_404(models.Item, id=item_id)
    if request.user != item.created_by and not request.user.is_superuser:
        return HttpResponseForbidden("You can only delete items you created")
    item.delete()
    notifications.notify_admins_of_item_change.delay(item, request.user, "deleted")  # type: ignore
    url = reverse("party", kwargs={"edition": item.party.edition})
    return redirect(url)


@login_required
@require_POST
def update_rsvp(request: HttpRequest, edition: str) -> HttpResponse:
    party = get_object_or_404(models.Party, edition=edition)
    if party.closed:
        return HttpResponseBadRequest("Party is closed")
    form = RsvpForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid form: {}".format(form.errors))
    try:
        person = models.Person.objects.get(id=form.cleaned_data["person_id"])
    except (models.Person.DoesNotExist, exceptions.ValidationError):
        return HttpResponseBadRequest("Invalid person_id")
    if request.user != person and not request.user.is_superuser:
        return HttpResponseBadRequest("You can only update your own RSVP")
    invite = models.Invite.objects.filter(party=party, person=person).first()
    if invite is None:
        return HttpResponseBadRequest("Not invited")
    old_status = invite.status
    with transaction.atomic():
        status = form.cleaned_data["rsvp"]
        if status.upper() in ("Y", "M"):
            if party.max_people and party.yes_count() >= party.max_people:
                return HttpResponseBadRequest("Party is full")
        invite.status = form.cleaned_data["rsvp"]
        if status.upper() == "N":
            invite.show_in_guest_list = False
        else:
            invite.show_in_guest_list = form.cleaned_data["show_in_guest_list"]
        invite.save()
        if invite.status == "N":
            items = models.Item.objects.filter(party=party, assigned_to=person)
            for item in items:
                item.assigned_to.remove(person)
                item.save()
    url = reverse("party", kwargs={"edition": party.edition})
    if old_status != invite.status:
        notifications.notify_admins_of_rsvp_change.delay(person, party, invite)
    return redirect(url)


@require_POST
def accept_cookies(request: HttpRequest) -> HttpResponse:
    request.session["cookie_accept"] = True
    return JsonResponse({"message": "Cookie accepted"})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    # Log out the user
    logout(request)

    # Get the URL of the previous page from the HTTP Referer header
    next_page = request.META.get("HTTP_REFERER")

    # If Referer is provided, strip the 'visitor_id' query param
    if next_page:
        url_parts = list(urlparse(next_page))
        query = parse_qs(url_parts[4])  # Query is the 4th element of the tuple
        query.pop("visitor_id", None)  # Remove 'visitor_id' if present
        url_parts[4] = urlencode(query, doseq=True)  # Re-encode the query string
        next_page = urlunparse(url_parts)

        return HttpResponseRedirect(next_page)
    else:
        return redirect("home")  # Replace with the name of your default route


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "slrportal/profile.html",
        {"person": request.user, "ingredients": [i.name for i in models.Ingredient.objects.all()]},
    )


@login_required()
@require_POST
def add_allergy(request: HttpRequest) -> HttpResponse:
    person = get_object_or_404(models.Person, id=request.user.id)
    allergy_name = request.POST.get("allergy")
    if allergy_name is None:
        return HttpResponseBadRequest("No allergy provided")
    ingredient, _ = models.Ingredient.objects.get_or_create(name=allergy_name)
    allergy, _ = models.Allergy.objects.get_or_create(ingredient=ingredient, person=person)
    return redirect("profile")


@login_required
@require_POST
def delete_allergy(request: HttpRequest, allergy_id: int) -> HttpResponse:
    allergy = get_object_or_404(models.Allergy, ingredient_id=allergy_id, person=request.user)

    # Check if the person deleting the allergy is the one who owns it
    if allergy.person != request.user:
        # If not, return an HTTP Forbidden response
        return HttpResponseForbidden()

    allergy.delete()
    # Redirect to the profile page, or wherever is appropriate
    return redirect("profile")  # Replace 'profile' with the name of your profile view


def privacy_policy(request: HttpRequest) -> HttpResponse:
    return render(request, "slrportal/privacy_policy.html")


def custom_404(request: HttpRequest, exception: Exception) -> HttpResponseNotFound:
    template = loader.get_template("404.html")
    context = {
        "request_path": request.path,
        # You can add more context variables here if needed
    }
    return HttpResponseNotFound(template.render(context, request))


@method_decorator(login_required, name="dispatch")
class DeleteProfileView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, "slrportal/confirm_delete_profile.html")

    def post(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        user.delete()
        return redirect("home")


# Add to urls.py
# path('delete-profile/', views.DeleteProfileView.as_view(), name='delete_profile'),
