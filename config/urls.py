from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("input/", include("input.urls")),
    path("simulation/", include("simulation.urls")),
    path("result/", include("result.urls")),
    path("api/", include("api.urls")),
    path("", RedirectView.as_view(url="/input/", permanent=True)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
