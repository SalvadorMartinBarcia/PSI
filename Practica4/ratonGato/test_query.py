import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ratonGato.settings')

import django

django.setup()
from datamodel.models import User, Game, Move, GameStatus


def query():
    id_aux = 10
    user = 'usuario10'
    password = 'contra10'
    u = User.objects.filter(id=id_aux)

    if u.exists():
        u10 = u[0]
        print("El usuario con id: %d ya existe" % id_aux)
    else:
        u10 = User(id=id_aux, password=password, username=user)
        u10.save()

    id_aux = 11
    user = 'usuario11'
    password = 'contra11'
    u = User.objects.filter(id=id_aux)

    if u.exists():
        u11 = u[0]
        print("El usuario con id: %d ya existe" % id_aux)
    else:
        u11 = User(id=id_aux, password=password, username=user)
        u11.save()

    g1 = Game(cat_user=u10)
    g1.save()

    games = Game.objects.filter(status=GameStatus.CREATED)

    if games.exists():
        print("Juegos no iniciados:")
        print(games)
        game = games[0]
        game.mouse_user = u11
        game.save()
        print("Juego al que ha entrado el raton")
        print(game)
    else:
        print("No existe ningun juego con un usuario vacio")
        exit()

    cat = game.cat_user
    if cat.id == 10:
        move = Move(game=game, origin=2, target=11, player=cat)
        move.save()
        print("Gato se mueve")

    mouse = game.mouse_user

    if mouse.id == 11:
        move2 = Move(game=game, origin=59, target=52, player=mouse)
        move2.save()
        print("Raton se mueve")


if __name__ == '__main__':
    query()
