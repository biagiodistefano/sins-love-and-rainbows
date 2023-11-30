from django.core import exceptions
from django.http import Http404, HttpResponse, HttpResponseNotAllowed
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone

from api import models
from .forms import ItemForm


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
    context = {'party': party, 'person': person}
    return render(request, 'slrportal/party_detail.html', context)


def assign_item(request: HttpRequest, item_id: str, person_id: str) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed("Only POST requests are allowed.")
    task = get_object_or_404(models.Item, id=item_id)
    person = get_object_or_404(models.Person, id=person_id)
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
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.party = party
            item.save()
            # You can redirect to the party detail page or wherever is appropriate
            url = reverse("party", kwargs={"edition": party.edition}) + f"?visitor_id={form.cleaned_data['person_id']}"
            if form.cleaned_data["claim"]:
                item.assigned_to.add(form.cleaned_data["person_id"])
            return redirect(url)
        return HttpResponse("Invalid form: {}".format(form.errors))

    return HttpResponseNotAllowed("Only POST requests are allowed.")
