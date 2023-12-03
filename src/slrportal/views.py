from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core import exceptions
from django.db import transaction
from django.http import (
    Http404, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseRedirect,
    JsonResponse,
)
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone

from api import models
from .forms import ItemForm, RsvpForm


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'slrportal/index.html', {'user': request.user})


def redirect_url(request: HttpRequest, short_url: str):
    instance = get_object_or_404(models.ShortUrl, short_url=short_url)
    return redirect(instance.url)


def get_next_party(request: HttpRequest) -> HttpResponse:
    try:
        next_party = models.Party.objects.filter(date_and_time__gte=timezone.now(), closed=False).earliest(
            'date_and_time'
        )
    except models.Party.DoesNotExist:
        raise Http404("No upcoming parties found.")
    url = reverse('party', kwargs={"edition": next_party.edition})
    return redirect(url)


def party_detail(request: HttpRequest, edition: str) -> HttpResponse:
    party = get_object_or_404(models.Party, edition=edition)
    invite = None
    if request.user.is_authenticated:
        invite = models.Invite.objects.filter(party=party, person=request.user).first()
    context = {'party': party, 'person': request.user, 'invite': invite}
    return render(request, 'slrportal/party_detail.html', context)


@login_required
def assign_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
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
    url = reverse("party", kwargs={"edition": task.party.edition})
    return redirect(url)


@login_required
def unassign_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
    task = get_object_or_404(models.Item, id=item_id)
    if task.party.closed:
        return HttpResponseBadRequest("Party is closed")
    person = get_object_or_404(models.Person, id=person_id)
    if request.user != person and not request.user.is_superuser:
        return HttpResponseBadRequest("You can only unassign items from yourself")
    task.assigned_to.remove(person)
    task.save()
    url = reverse("party", kwargs={"edition": task.party.edition})
    return redirect(url)


@login_required
def add_item(request: HttpRequest, edition: str) -> HttpResponse:
    if not request.method == 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
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
    if form.cleaned_data["claim"]:
        item.assigned_to.add(form.cleaned_data["person_id"])
    return redirect(url)


@login_required
def update_rsvp(request: HttpRequest, edition: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
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
    with transaction.atomic():
        invite.status = form.cleaned_data["rsvp"]
        invite.save()
        if invite.status == "N":
            items = models.Item.objects.filter(party=party, assigned_to=person)
            for item in items:
                item.assigned_to.remove(person)
                item.save()
    url = reverse("party", kwargs={"edition": party.edition})
    return redirect(url)


def accept_cookies(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
    request.session["cookie_accept"] = True
    return JsonResponse({"message": "Cookie accepted"})


def logout_view(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")

    # Log out the user
    logout(request)

    # Get the URL of the previous page from the HTTP Referer header
    next_page = request.META.get('HTTP_REFERER')

    # If Referer is provided, strip the 'visitor_id' query param
    if next_page:
        url_parts = list(urlparse(next_page))
        query = parse_qs(url_parts[4])  # Query is the 4th element of the tuple
        query.pop('visitor_id', None)  # Remove 'visitor_id' if present
        url_parts[4] = urlencode(query, doseq=True)  # Re-encode the query string
        next_page = urlunparse(url_parts)

        return HttpResponseRedirect(next_page)
    else:
        return redirect('home')  # Replace with the name of your default route
