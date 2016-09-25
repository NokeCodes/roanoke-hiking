from django.http import JsonResponse
from django.shortcuts import render

from .hikes import get_all_hikes


def hikes(request):
    hikes = get_all_hikes()
    return JsonResponse({'hikes': hikes})
