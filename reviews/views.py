from itertools import chain

from django.contrib.auth.decorators import login_required
from django.db.models import CharField, Value, Q
from django.shortcuts import render, redirect, get_object_or_404

from . import forms
from . import models


@login_required
def home(request):

    # get user feed tickets and reviews
    user_tickets = models.Ticket.objects.filter(
        Q(user__in=request.user.following.values("followed_user")) |
        Q(user=request.user)
    )
    user_tickets = user_tickets.annotate(
        content_type=Value('TICKET', CharField()))
    user_reviews = models.Review.objects.filter(
        Q(user__in=request.user.following.values("followed_user")) |
        Q(user=request.user) |
        Q(ticket__in=models.Ticket.objects.filter(user=request.user))
    )
    user_reviews = user_reviews.annotate(
        content_type=Value('REVIEW', CharField()))

    user_feed = sorted(
        chain(user_tickets, user_reviews),
        key=lambda instance: instance.time_created,
        reverse=True
    )[:3]

    # get general feed tickets and reviews
    general_tickets = models.Ticket.objects.all()
    general_tickets = general_tickets.annotate(
        content_type=Value('TICKET', CharField()))
    general_reviews = models.Review.objects.all()
    general_reviews = general_reviews.annotate(
        content_type=Value('REVIEW', CharField()))

    general_feed = sorted(
        chain(general_tickets, general_reviews),
        key=lambda instance: instance.time_created,
        reverse=True
    )[:3]

    context = {'user_feed': user_feed,
               'general_feed': general_feed}
    return render(request, 'reviews/home.html', context)


@login_required
def feed(request):
    tickets = models.Ticket.objects.filter(
        Q(user__in=request.user.following.values("followed_user")) |
        Q(user=request.user)
    )
    tickets = tickets.annotate(
        content_type=Value('TICKET', CharField()))

    reviews = models.Review.objects.filter(
        Q(user__in=request.user.following.values("followed_user")) |
        Q(user=request.user) |
        Q(ticket__in=models.Ticket.objects.filter(user=request.user))
    )
    reviews = reviews.annotate(
        content_type=Value('REVIEW', CharField()))

    feed = sorted(
        chain(tickets, reviews),
        key=lambda instance: instance.time_created,
        reverse=True
    )

    context = {'feed': feed}
    return render(request, 'reviews/feed.html', context)


@login_required
def posts(request):
    tickets = models.Ticket.objects.filter(user=request.user)
    tickets = tickets.annotate(content_type=Value('TICKET', CharField()))
    reviews = models.Review.objects.filter(user=request.user)
    reviews = reviews.annotate(content_type=Value('REVIEW', CharField()))

    feed = sorted(
        chain(tickets, reviews),
        key=lambda instance: instance.time_created,
        reverse=True
    )
    context = {'feed': feed}
    return render(request, 'reviews/posts.html', context)


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = forms.TicketForm(request.POST, request.FILES)
        if form.is_valid():
            # form is valid save ticket in DB
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()

            next = request.POST.get('next', '/')
            # go to previous page
            return redirect(next)
    else:
        form = forms.TicketForm()

    context = {'form': form}
    return render(request, 'reviews/ticket_create.html', context)


@login_required
def ticket_edit(request, ticket_id):
    ticket = get_object_or_404(models.Ticket, id=ticket_id)
    form = forms.TicketForm(instance=ticket)
    if request.method == 'POST':
        form = forms.TicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            # form is valid save ticket in DB
            form.save()

            next = request.POST.get('next', '/')
            # go to previous page
            return redirect(next)

    context = {'form': form}
    return render(request, 'reviews/ticket_edit.html', context)


@login_required
def ticket_delete(request, ticket_id):
    ticket = models.Ticket.objects.get(id=ticket_id)

    if request.method == 'POST':
        ticket.delete()
        return redirect('home')

    context = {'ticket': ticket}
    return render(request,
                  'reviews/ticket_delete.html',
                  context)


@login_required
def review_without_ticket_create(request):
    """ create a ticket AND a review at the same time"""
    if request.method == 'POST':
        ticket_form = forms.TicketForm(request.POST, request.FILES)
        review_form = forms.ReviewForm(request.POST)
        if all([ticket_form.is_valid(), review_form.is_valid()]):
            # all form are valid save ticket anr review in DB
            ticket = ticket_form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            review = review_form.save(commit=False)
            review.user = request.user
            review.ticket = ticket
            review.save()

            next = request.POST.get('next', '/')
            # go to previous page
            return redirect(next)
    else:
        ticket_form = forms.TicketForm()
        review_form = forms.ReviewForm()

    context = {'ticket_form': ticket_form,
               'review_form': review_form
               }
    return render(request, 'reviews/review_without_ticket_create.html',
                  context)


@login_required
def review_with_ticket_create(request, ticket_id):
    """ create a review from a ticket"""
    ticket = get_object_or_404(models.Ticket, id=ticket_id)

    if request.method == 'POST':
        review_form = forms.ReviewForm(request.POST)
        if review_form.is_valid():
            # save review in DB
            review = review_form.save(commit=False)
            review.user = request.user
            review.ticket = ticket
            review.save()

            next = request.POST.get('next', '/')
            # go to previous page
            return redirect(next)
    else:
        review_form = forms.ReviewForm()

    context = {'ticket': ticket,
               'review_form': review_form
               }
    return render(request, 'reviews/review_with_ticket_create.html',
                  context)


@login_required
def review_edit(request, review_id):
    """ edit a review"""
    review = get_object_or_404(models.Review, id=review_id)
    review_form = forms.ReviewForm(instance=review)
    ticket = get_object_or_404(models.Ticket, id=review.ticket.id)

    if request.method == 'POST':
        review_form = forms.ReviewForm(request.POST, instance=review)
        if review_form.is_valid():
            # save review in DB
            review_form.save()

            next = request.POST.get('next', '/')
            # go to previous page
            return redirect(next)

    context = {'ticket': ticket,
               'review_form': review_form
               }
    return render(request, 'reviews/review_edit.html',
                  context)


@login_required
def review_delete(request, review_id):
    review = models.Review.objects.get(id=review_id)

    if request.method == 'POST':
        review.delete()
        return redirect('home')

    context = {'review': review}
    return render(request,
                  'reviews/review_delete.html',
                  context)


@login_required
def follow_user(request):
    """ add a followed user"""
    followed_by = request.user.followed_by.all()
    following = request.user.following.all()
    if request.method == 'POST':
        form = forms.FollowUserForm(request.POST)
        if form.is_valid():
            # save review in DB
            user_follows = form.save(commit=False)
            user_follows.user = request.user
            user_follows = form.save()
            # go back to home page
            return redirect('follow_user')
    else:
        form = forms.FollowUserForm()

    context = {'form': form,
               'following': following,
               'followed_by': followed_by
               }
    return render(request, 'reviews/follow_user.html',
                  context)


@login_required
def unfollow_user(request, follow_id):
    relationship = models.UserFollows.objects.get(id=follow_id)

    if request.method == 'POST':
        relationship.delete()
        return redirect('follow_user')

    context = {'relationship': relationship}
    return render(request,
                  'reviews/follow_delete.html',
                  context)
