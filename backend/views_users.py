# backend/views_users.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

from .decorators import permission_required
from .models import Role, UserProfile, Invitation
from .email import send_invitation_email


@permission_required('users.read')
def UserListView(request):
    users = User.objects.select_related('profile__role').order_by('-date_joined')
    return render(request, 'users/users.html', {'users': users})


@permission_required('users.create')
def UserCreateView(request):
    roles = Role.objects.all()
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        role_id   = request.POST.get('role')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'users/user-create.html', {'roles': roles})

        user = User.objects.create_user(username=username, email=email, password=password)
        role = Role.objects.filter(pk=role_id).first()
        UserProfile.objects.create(user=user, role=role)
        messages.success(request, f'User "{username}" created.')
        return redirect('users')

    return render(request, 'users/user-create.html', {'roles': roles})


@permission_required('users.update')
def UserEditView(request, id):
    user_obj = get_object_or_404(User, pk=id)
    roles    = Role.objects.all()

    if request.method == 'POST':
        user_obj.email     = request.POST.get('email', user_obj.email)
        user_obj.first_name = request.POST.get('first_name', user_obj.first_name)
        user_obj.last_name  = request.POST.get('last_name', user_obj.last_name)
        user_obj.save()

        role_id = request.POST.get('role')
        role    = Role.objects.filter(pk=role_id).first()
        profile, _ = UserProfile.objects.get_or_create(user=user_obj)
        profile.role = role
        profile.save()

        messages.success(request, 'User updated.')
        return redirect('users')

    return render(request, 'users/user-edit.html', {'user_obj': user_obj, 'roles': roles})


@permission_required('users.delete')
def UserDeleteView(request, id):
    user_obj = get_object_or_404(User, pk=id)
    if request.method == 'POST':
        user_obj.delete()
        return JsonResponse({'message': 'User deleted.', 'status': 'success'})
    return JsonResponse({'error': 'Invalid'}, status=400)


@permission_required('users.create')
def InviteUserView(request):
    roles = Role.objects.all()
    if request.method == 'POST':
        email   = request.POST.get('email', '').strip()
        role_id = request.POST.get('role')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'users/user-invite.html', {'roles': roles})

        role       = Role.objects.filter(pk=role_id).first()
        expiry     = timezone.now() + timedelta(days=getattr(settings, 'INVITATION_EXPIRY_DAYS', 7))
        invitation = Invitation.objects.create(
            email=email, role=role,
            invited_by=request.user, expires_at=expiry
        )

        accept_url = request.build_absolute_uri(f'/invite/accept/{invitation.token}/')
        try:
            send_invitation_email(
                to_email=email,
                accept_url=accept_url,
                expiry_days=getattr(settings, 'INVITATION_EXPIRY_DAYS', 7),
            )
            messages.success(request, f'Invitation email sent to {email}.')
            return redirect('users')
        except Exception as e:
            # Email failed — stay on page and show the manual link prominently
            return render(request, 'users/user-invite.html', {
                'roles':      roles,
                'email_error': str(e),
                'accept_url': accept_url,
                'invite_email': email,
            })

    return render(request, 'users/user-invite.html', {'roles': roles})


def AcceptInviteView(request, token):
    invitation = get_object_or_404(Invitation, token=token)

    if invitation.status != 'Pending':
        messages.error(request, 'This invitation is no longer valid.')
        return redirect('login')

    if invitation.expires_at < timezone.now():
        invitation.status = 'Expired'
        invitation.save()
        messages.error(request, 'This invitation has expired.')
        return redirect('login')

    # Existing user with this email?
    existing_user = User.objects.filter(email=invitation.email).first()
    if existing_user:
        profile, _ = UserProfile.objects.get_or_create(user=existing_user)
        if invitation.role:
            profile.role = invitation.role
            profile.save()
        invitation.status = 'Accepted'
        invitation.save()
        messages.success(request, 'Your role has been updated. Please log in.')
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'users/invite-accept.html', {'invitation': invitation})

        new_user = User.objects.create_user(
            username=username,
            email=invitation.email,
            password=password,
        )
        UserProfile.objects.create(user=new_user, role=invitation.role)
        invitation.status = 'Accepted'
        invitation.save()
        messages.success(request, 'Account created! Please log in.')
        return redirect('login')

    return render(request, 'users/invite-accept.html', {'invitation': invitation})
