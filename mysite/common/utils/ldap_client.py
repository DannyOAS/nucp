import ldap
import ldap.modlist  # Import modlist explicitly
import logging
import hashlib
import os
import base64
from django.conf import settings

logger = logging.getLogger(__name__)

class LDAPClient:
    """
    Utility class for interacting with the LDAP server.
    """
    
    def __init__(self):
        self.server_uri = getattr(settings, 'AUTH_LDAP_SERVER_URI', 'ldap://10.88.89.156:389')
        self.bind_dn = getattr(settings, 'AUTH_LDAP_BIND_DN', 'cn=admin,dc=isnord,dc=ca')
        self.bind_password = getattr(settings, 'AUTH_LDAP_BIND_PASSWORD', 'g654D!')
        self.base_dn = 'dc=isnord,dc=ca'
        self.people_dn = f'ou=people,{self.base_dn}'
        self.groups_dn = f'ou=groups,{self.base_dn}'
        self.providers_dn = f'cn=providers,{self.groups_dn}'
        
        self.conn = None
        
    def connect(self):
        """Establish a connection to the LDAP server."""
        try:
            self.conn = ldap.initialize(self.server_uri)
            self.conn.protocol_version = ldap.VERSION3
            self.conn.simple_bind_s(self.bind_dn, self.bind_password)
            return True
        except ldap.LDAPError as e:
            logger.error(f"LDAP connection error: {e}")
            return False
    
    def disconnect(self):
        """Close the LDAP connection."""
        if self.conn:
            self.conn.unbind_s()
            self.conn = None
    
    def user_exists(self, username):
        """Check if a user exists in LDAP."""
        if not self.conn:
            if not self.connect():
                return False
                
        try:
            result = self.conn.search_s(
                self.people_dn, 
                ldap.SCOPE_SUBTREE, 
                f'(uid={username})'
            )
            return len(result) > 0
        except ldap.LDAPError as e:
            logger.error(f"LDAP search error: {e}")
            return False
    
    def create_user(self, user_data):
        """
        Create a new user in LDAP.
        
        Args:
            user_data: Dictionary containing user details including:
                - username
                - first_name
                - last_name
                - email
                - password_hash (SSHA hashed password)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.conn:
            if not self.connect():
                return False
        
        # Get a unique UID/GID number (simple approach)
        try:
            result = self.conn.search_s(
                self.people_dn,
                ldap.SCOPE_SUBTREE,
                '(objectClass=posixAccount)',
                ['uidNumber']
            )
            # Find the highest uidNumber and add 1
            uid_numbers = [int(entry[1]['uidNumber'][0]) for entry in result if 'uidNumber' in entry[1]]
            next_uid = max(uid_numbers) + 1 if uid_numbers else 10000
        except ldap.LDAPError as e:
            logger.error(f"Error getting next UID: {e}")
            next_uid = 10000  # Fallback
            
        username = user_data.get('username')
        dn = f'uid={username},{self.people_dn}'
        
        # Prepare LDAP attributes
        attrs = {
            'objectClass': [b'inetOrgPerson', b'posixAccount', b'shadowAccount'],
            'uid': [username.encode('utf-8')],
            'cn': [f"{user_data.get('first_name')} {user_data.get('last_name')}".encode('utf-8')],
            'sn': [user_data.get('last_name', '').encode('utf-8')],
            'givenName': [user_data.get('first_name', '').encode('utf-8')],
            'displayName': [f"Dr. {user_data.get('first_name')} {user_data.get('last_name')}".encode('utf-8')],
            'mail': [user_data.get('email', '').encode('utf-8')],
            'userPassword': [user_data.get('password_hash', '').encode('utf-8')],
            'uidNumber': [str(next_uid).encode('utf-8')],
            'gidNumber': [str(next_uid).encode('utf-8')],
            'homeDirectory': [f"/home/{username}".encode('utf-8')],
            'loginShell': [b'/bin/bash'],
            'gecos': [b'Provider User'],
            'shadowExpire': [b'-1'],
            'shadowFlag': [b'0'],
            'shadowWarning': [b'7'],
            'shadowMin': [b'8'],
            'shadowMax': [b'999999'],
            'shadowLastChange': [b'10877']
        }
        
        # Add title if provided
        if 'title' in user_data:
            attrs['title'] = [user_data.get('title', '').encode('utf-8')]
        
        try:
            # Add the new user
            self.conn.add_s(dn, ldap.modlist.addModlist(attrs))
            logger.info(f"Created LDAP user: {username}")
            return True
        except ldap.LDAPError as e:
            logger.error(f"Error creating user in LDAP: {e}")
            return False
    
    def add_user_to_group(self, username, group_dn):
        """
        Add a user to an LDAP group.
        
        Args:
            username: Username (uid) of the user to add
            group_dn: Distinguished name of the group
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.conn:
            if not self.connect():
                return False
                
        user_dn = f'uid={username},{self.people_dn}'
        
        # Check if user is already in the group
        try:
            result = self.conn.search_s(
                group_dn,
                ldap.SCOPE_BASE,
                '(objectClass=*)',
                ['member']
            )
            
            if result and 'member' in result[0][1]:
                members = [m.decode('utf-8') for m in result[0][1]['member']]
                if user_dn in members:
                    logger.info(f"User {username} is already in group {group_dn}")
                    return True
        except ldap.LDAPError as e:
            logger.error(f"Error checking group membership: {e}")
            return False
        
        # Add user to group
        try:
            mod_attrs = [(ldap.MOD_ADD, 'member', user_dn.encode('utf-8'))]
            self.conn.modify_s(group_dn, mod_attrs)
            logger.info(f"Added user {username} to group {group_dn}")
            return True
        except ldap.LDAPError as e:
            logger.error(f"Error adding user to group: {e}")
            return False
    
    def add_user_to_providers(self, username):
        """Add a user to the providers group."""
        return self.add_user_to_group(username, self.providers_dn)
    
    def generate_password_hash(self, password):
        """Generate an SSHA password hash for LDAP."""
        # Generate a salt
        salt = os.urandom(4)
        
        # Hash the password and salt
        sha = hashlib.sha1(password.encode('utf-8'))
        sha.update(salt)
        
        # Create SSHA digest
        ssha_digest = sha.digest() + salt
        
        # Base64 encode and return with {SSHA} prefix
        return '{SSHA}' + base64.b64encode(ssha_digest).decode('utf-8')
