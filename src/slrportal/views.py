from django.core import exceptions
from django.http import Http404, HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.db import transaction
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

    return redirect('party', edition=next_party.edition)


def party_detail(request: HttpRequest, edition: str) -> HttpResponse:
    party = get_object_or_404(models.Party, edition=edition)
    try:
        visitor_id = request.GET.get('visitor_id', None)
        person = models.Person.objects.get(id=visitor_id)
    except (models.Person.DoesNotExist, exceptions.ValidationError):
        person = None
    if request.user.is_authenticated:
        person = request.user
    invite = models.Invite.objects.filter(party=party, person=person).first()
    context = {'party': party, 'person': person, 'invite': invite}
    return render(request, 'slrportal/party_detail.html', context)


def assign_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
    task = get_object_or_404(models.Item, id=item_id)
    person = get_object_or_404(models.Person, id=person_id)
    invite = models.Invite.objects.filter(party=task.party, person=person).first()
    if invite is None:
        return HttpResponseBadRequest("Not invited")
    if invite.status == "N":
        return HttpResponseBadRequest("Not attending")
    task.assigned_to.add(person)
    task.save()
    url = reverse("party", kwargs={"edition": task.party.edition}) + f"?visitor_id={person.id}"
    return redirect(url)


def unassign_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
    task = get_object_or_404(models.Item, id=item_id)
    person = get_object_or_404(models.Person, id=person_id)
    task.assigned_to.remove(person)
    task.save()
    url = reverse("party", kwargs={"edition": task.party.edition}) + f"?visitor_id={person.id}"
    return redirect(url)


def add_item(request: HttpRequest, edition: str) -> HttpResponse:
    party = get_object_or_404(models.Party, edition=edition)
    if not request.method == 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
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
    # You can redirect to the party detail page or wherever is appropriate
    url = reverse("party", kwargs={"edition": party.edition}) + f"?visitor_id={person_id}"
    if form.cleaned_data["claim"]:
        item.assigned_to.add(form.cleaned_data["person_id"])
    return redirect(url)


def update_rsvp(request: HttpRequest, edition: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
    party = get_object_or_404(models.Party, edition=edition)
    form = RsvpForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest("Invalid form: {}".format(form.errors))
    try:
        person = models.Person.objects.get(id=form.cleaned_data["person_id"])
    except (models.Person.DoesNotExist, exceptions.ValidationError):
        return HttpResponseBadRequest("Invalid person_id")
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
    url = reverse("party", kwargs={"edition": party.edition}) + f"?visitor_id={person.id}"
    return redirect(url)
