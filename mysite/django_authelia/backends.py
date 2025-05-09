from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend
from provider.models import Provider

class AutheliaBackend(ModelBackend):
    """
    Authentication backend for Authelia.
    """
    
    def authenticate(self, request, username=None, email=None, remote_name=None, remote_groups=None, **kwargs):
        if not username:
            return None
            
        # Get or create user
        try:
            user = User.objects.get(username=username)
            # Update user attributes if needed
            user_updated = False
            
            # Update email if provided and different
            if email and user.email != email:
                user.email = email
                user_updated = True
                
            # Update name if provided
            if remote_name:
                names = remote_name.split(' ', 1)
                first_name = names[0]
                last_name = names[1] if len(names) > 1 else ''
                
                if user.first_name != first_name:
                    user.first_name = first_name
                    user_updated = True
                    
                if user.last_name != last_name:
                    user.last_name = last_name
                    user_updated = True
            
            if user_updated:
                user.save()
                
        except User.DoesNotExist:
            # Create new user
            names = remote_name.split(' ', 1) if remote_name else ['', '']
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            
            user = User.objects.create_user(
                username=username,
                email=email or '',
                first_name=first_name,
                last_name=last_name
            )
        
        # Update group membership based on remote_groups
        if remote_groups:
            self._update_user_groups(user, remote_groups)
            
        # Create or update Provider record for users in the providers group
        if user.groups.filter(name='providers').exists():
            provider, created = Provider.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': f'TMP{user.id}',
                    'specialty': 'General',
                    'is_active': True
                }
            )
            
        return user
    
    def _update_user_groups(self, user, remote_groups):
        """Update the user's group membership based on Authelia groups."""
        # Parse remote_groups (comma-separated)
        group_names = [g.strip() for g in remote_groups.split(',') if g.strip()]
        
        # Get or create the corresponding Django groups
        for group_name in group_names:
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        
        # Remove user from groups not in the list
        current_groups = user.groups.all()
        groups_to_remove = [g for g in current_groups if g.name not in group_names]
        for group in groups_to_remove:
            user.groups.remove(group)
