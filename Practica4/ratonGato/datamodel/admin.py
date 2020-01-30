from django.contrib import admin

from .models import Game, Counter, Move

admin.site.register(Counter)
admin.site.register(Game)
admin.site.register(Move)

