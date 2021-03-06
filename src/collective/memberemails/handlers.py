from zope.component import getUtility
from plone.registry.interfaces import IRegistry

from DateTime import DateTime
from Products.CMFCore.utils import getToolByName

from collective.memberemails.interfaces import IMemberEmailsSettings


def collect_data(site, userid):
    portal_url = site.absolute_url()
    reset = site.portal_password_reset.requestReset(userid)
    mt = getToolByName(site, 'portal_membership')
    member = mt.getMemberById(userid)
    return {'approval_url': portal_url + '/@@user-approval?userid=' + userid,
            'approve_url': portal_url + '/@@user-approve?userid=' + userid,
            'disapprove_url': portal_url + '/@@user-disapprove?userid=' + userid,
            'userinfo_url': portal_url + '/@@user-information?userid=' + userid,
            'userid': userid,
            'fullname': member.getProperty('fullname'),
            'pwreset_url': site.pwreset_constructURL(reset['randomstring'])+'?userid='+userid,
            'portal_url': portal_url}
     
    
def userAddedHandler(site, event):
    registry = getUtility(IRegistry)
  
    try:
        settings = registry.forInterface(IMemberEmailsSettings)
    except KeyError:
        # The product is not installed
        return

    if not settings.enabled:
        return
        
    data = collect_data(site, event.userid)
    email = settings.registration_email.format(**data)
    mailhost = getToolByName(site, 'MailHost')
    
    if settings.notification_address:
        address = settings.notification_address
    else:
        address = site.getProperty('email_from_address')
        
    mailhost.send(email, address, site.getProperty('email_from_address'), site.getProperty('email_encoding'))

def userApprovedHandler(site, event):
    registry = getUtility(IRegistry)
  
    try:
        settings = registry.forInterface(IMemberEmailsSettings)
    except KeyError:
        # The product is not installed
        return

    if not settings.enabled:
        return
        
    data = collect_data(site, event.userid)
    email = settings.approval_email.format(**data)
    mailhost = getToolByName(site, 'MailHost')
    
    acl_users = getToolByName(site, 'acl_users')
    user = acl_users.getUser(event.userid)
    address = user.getProperty('email')
    if not address:
        return
        
    mailhost.send(email, address, site.getProperty('email_from_address'), site.getProperty('email_encoding'))

def userDisapprovedHandler(site, event):
    registry = getUtility(IRegistry)
  
    try:
        settings = registry.forInterface(IMemberEmailsSettings)
    except KeyError:
        # The product is not installed
        return

    if not settings.enabled:
        return
        
    data = collect_data(site, event.userid)
    email = settings.disapproval_email.format(**data)
    mailhost = getToolByName(site, 'MailHost')
    
    acl_users = getToolByName(site, 'acl_users')
    user = acl_users.getUser(event.userid)
    address = user.getProperty('email')
    if not address:
        return
        
    mailhost.send(email, address, site.getProperty('email_from_address'), site.getProperty('email_encoding'))

def userRemoveHandler(site, event):
    """Send the disapproved email if the user is being removed without being approved
       or dissaproved and has never logged in."""
    registry = getUtility(IRegistry)
  
    try:
        settings = registry.forInterface(IMemberEmailsSettings)
    except KeyError:
        # The product is not installed
        return

    if not settings.enabled:
        return
        
    data = collect_data(site, event.userid)
    email = settings.disapproval_email.format(**data)
    mailhost = getToolByName(site, 'MailHost')
    
    acl_users = getToolByName(site, 'acl_users')
    
    status = acl_users.userStatus(event.userid)
    if status is not None:
        # The user has been approved or disapproved. This is therefore not a 
        # disapproval event but a removal.
        # We don't send an email.
        return
    
    user = acl_users.getUser(event.userid)
    address = user.getProperty('email')
    if not address:
        return
        
    mailhost.send(email, address, site.getProperty('email_from_address'), site.getProperty('email_encoding'))
