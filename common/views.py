from django.shortcuts import render


def menu_placeholder(request, page_title, page_message, sidebar_title="Menu"):
    return render(
        request,
        "components/menu_placeholder.html",
        {
            "page_title": page_title,
            "page_message": page_message,
            "sidebar_title": sidebar_title,
        },
    )
