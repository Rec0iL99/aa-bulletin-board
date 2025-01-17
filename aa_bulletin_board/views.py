"""
The views
"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Prefetch
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# AA Bulletin Board
from aa_bulletin_board.forms import Bulletin, BulletinForm


@login_required
@permission_required(perm="aa_bulletin_board.basic_access")
def dashboard(request: WSGIRequest) -> HttpResponse:
    """
    Index view

    :param request:
    :type request:
    :return:
    :rtype:
    """

    bulletins = (
        Bulletin.objects.prefetch_related(
            Prefetch(lookup="groups", queryset=Group.objects.order_by("name"))
        )
        .user_has_access(user=request.user)
        .order_by("-created_date")
    )
    context = {"bulletins": bulletins}

    return render(
        request=request,
        template_name="aa_bulletin_board/dashboard.html",
        context=context,
    )


@login_required
@permission_required(perm="aa_bulletin_board.manage_bulletins")
def create_bulletin(request: WSGIRequest) -> HttpResponse:
    """
    Edit an existing bulletin

    :param request:
    :type request:
    :return:
    :rtype:
    """

    if request.method == "POST":
        # Create a form instance and populate it with data
        form = BulletinForm(data=request.POST)

        # Check whether it's valid:
        if form.is_valid():
            bulletin__title = form.cleaned_data["title"]
            bulletin__content = form.cleaned_data["content"]
            bulletin__created_date = timezone.now()

            bulletin = Bulletin()
            bulletin.title = bulletin__title
            bulletin.content = bulletin__content
            bulletin.created_date = bulletin__created_date
            bulletin.created_by = request.user
            bulletin.save()

            bulletin.groups.set(  # pylint: disable=no-member
                form.cleaned_data["groups"]
            )

            messages.success(
                request=request, message=_(f'Bulletin "{bulletin__title}" created.')
            )

            return redirect(to="aa_bulletin_board:view_bulletin", slug=bulletin.slug)
    else:
        form = BulletinForm()

    context = {"form": form, "bulletin": False}

    return render(
        request=request,
        template_name="aa_bulletin_board/edit-bulletin.html",
        context=context,
    )


@login_required
@permission_required(perm="aa_bulletin_board.basic_access")
def view_bulletin(request: WSGIRequest, slug: str) -> HttpResponse:
    """
    View a bulletin

    :param request:
    :type request:
    :param slug:
    :type slug:
    :return:
    :rtype:
    """

    try:
        bulletin = Bulletin.objects.user_has_access(request.user).get(slug=slug)
        context = {"bulletin": bulletin, "slug": slug}

        return render(
            request=request,
            template_name="aa_bulletin_board/bulletin.html",
            context=context,
        )
    except Bulletin.DoesNotExist:  # pylint: disable=no-member
        messages.warning(
            request=request,
            message=_(
                "The bulletin you are looking for does either not exist, or you don't "
                "have access to it."
            ),
        )

        return redirect(to="aa_bulletin_board:dashboard")


@login_required
@permission_required(perm="aa_bulletin_board.manage_bulletins")
def edit_bulletin(request: WSGIRequest, slug: str) -> HttpResponse:
    """
    Edit an existing bulletin

    :param request:
    :type request:
    :param slug:
    :type slug:
    :return:
    :rtype:
    """

    try:
        bulletin = Bulletin.objects.get(slug=slug)

        if request.method == "POST":
            # Create a form instance and populate it with data
            form = BulletinForm(data=request.POST, instance=bulletin)

            # Check whether it's valid:
            if form.is_valid():
                bulletin__title = form.cleaned_data["title"]
                bulletin__content = form.cleaned_data["content"]
                bulletin__updated_date = timezone.now()

                bulletin.title = bulletin__title
                bulletin.content = bulletin__content
                bulletin.updated_date = bulletin__updated_date
                bulletin.groups.set(form.cleaned_data["groups"])
                bulletin.save()

                messages.success(
                    request=request, message=_(f'Bulletin "{bulletin__title}" updated.')
                )

                return redirect(
                    to="aa_bulletin_board:view_bulletin", slug=bulletin.slug
                )
        else:
            form = BulletinForm(instance=bulletin)

        context = {"form": form, "existing_bulletin": True, "bulletin": bulletin}

        return render(
            request=request,
            template_name="aa_bulletin_board/edit-bulletin.html",
            context=context,
        )
    except Bulletin.DoesNotExist:  # pylint: disable=no-member
        messages.warning(
            request=request,
            message=_("The bulletin you are trying to edit does not exist."),
        )

        return redirect(to="aa_bulletin_board:dashboard")


@login_required
@permission_required("aa_bulletin_board.manage_bulletins")
def remove_bulletin(request: WSGIRequest, slug: str) -> HttpResponseRedirect:
    """
    Remove bulletin

    :param request:
    :type request:
    :param slug:
    :type slug:
    :return:
    :rtype:
    """

    try:
        bulletin = Bulletin.objects.get(slug=slug)

        messages.success(
            request=request, message=_(f'Bulletin "{bulletin.title}" deleted.')
        )

        bulletin.delete()
    except Bulletin.DoesNotExist:  # pylint: disable=no-member
        messages.warning(
            request=request,
            message=_("The bulletin you are trying to delete does not exist."),
        )

    return redirect(to="aa_bulletin_board:dashboard")
