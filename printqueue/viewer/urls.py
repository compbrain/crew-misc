from django.conf.urls.defaults import *
from views import JSONQueueView, QueueView

urlpatterns = patterns('django.views.generic.simple',
    url(r'^$', 'direct_to_template', {'template': 'viewer/printindex.html'},
        name='viewer-index'),
)

urlpatterns += patterns('printqueue.viewer.views',
    (r'^printqueue/(.*)/json/$', 'JSONQueueView'),
    (r'^printqueue/(.*)/$', 'QueueView'),
)
