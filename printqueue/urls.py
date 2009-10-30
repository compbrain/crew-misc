from django.conf.urls.defaults import *
from django.conf import settings
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_DOC_ROOT}),
    (r'^$', 'printqueue.viewer.views.Index'),
    (r'^printqueue/(.*)/json/$', 'printqueue.viewer.views.JSONQueueView'),
    (r'^printqueue/(.*)/$', 'printqueue.viewer.views.QueueView'),

)
