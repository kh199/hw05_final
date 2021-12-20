from django.utils import timezone


def year(request):
    today = timezone.now()
    return {
        'year': today.year
    }
