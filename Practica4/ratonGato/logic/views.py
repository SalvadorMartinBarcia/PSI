import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as mylogout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponse, JsonResponse
from django.shortcuts import render, render_to_response

from datamodel import constants
from datamodel.models import Counter, Game, Move, GameStatus
from logic.forms import SignupForm, MoveForm, LogInForm


def anonymous_required(f):
    def wrapped(request):
        if request.user.is_authenticated:
            return HttpResponseForbidden(
                errorHTTP(request, exception=constants.MSG_ERROR_ANONYMOUS))
        else:
            return f(request)

    return wrapped


def errorHTTP(request, exception=None):
    inc_counter(request)
    context_dict = {}
    context_dict[constants.ERROR_MESSAGE_ID] = exception
    return render(request, "mouse_cat/error.html", add_counter_to_context(request, context_dict))


def index(request):
    context_dict = dict()
    return render(request, "mouse_cat/index.html", add_counter_to_context(request, context_dict))


@anonymous_required
def login_service(request):
    if request.method == 'POST':
        user_form = LogInForm(request=request, data=request.POST)
        if user_form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(username=username, password=password)

            login(request, user)

            request.session['counter'] = 0
            return render(request, 'mouse_cat/index.html')

        context_dict = {'user_form': user_form}
        return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))
    else:
        user_form = LogInForm()
        context_dict = {'user_form': user_form}
        return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


@login_required
def logout_service(request):
    user = request.user
    mylogout(request)
    request.session['counter'] = 0
    context_dict = {'user': user}
    return render(request, 'mouse_cat/logout.html', add_counter_to_context(request, context_dict))


@anonymous_required
def signup_service(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            if password == password2:
                user = None
                try:
                    user = User.objects.get(username=username)
                except:
                    pass
                if user is None:
                    user = User.objects.create_user(username=username, password=password)
                    user.save()
                    login(request, user)
                    request.session['counter'] = 0
                    context_dict = dict()
                    return render(request, "mouse_cat/index.html", add_counter_to_context(request, context_dict))
                else:
                    form.add_error(None, constants.MSG_ERROR_EXISTING_USER)
                    context_dict = {"user_form": form}
            else:
                form.add_error(None, constants.MSG_ERROR_DIFFERENT_PASSWORDS)
                context_dict = {"user_form": form}
        else:
            form.add_error(None, constants.MSG_ERROR_INVALID_PASSWORD)
            context_dict = {"user_form": form}
    else:
        form = SignupForm()
        context_dict = {'user_form': form}

    return render(request, 'mouse_cat/signup.html', add_counter_to_context(request, context_dict))


def add_counter_to_context(request, context_dict):
    if 'counter' in request.session:
        request.session['counter'] += 0
    else:
        request.session['counter'] = 0

    counter_global = Counter.objects.get_current_value()
    context_dict['counter_session'] = request.session['counter']
    context_dict['counter_global'] = counter_global
    return context_dict


def inc_counter(request):
    if 'counter' in request.session:
        request.session['counter'] += 1
    else:
        request.session['counter'] = 1

    Counter.objects.inc()


def create_game_service(request):
    if request.user.is_authenticated:
        game = Game(cat_user=request.user)
        game.save()
        return render(request, "mouse_cat/new_game.html", {'game': game})
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def select_join_service(request):
    if request.user.is_authenticated:
        game_list = Game.objects.filter(mouse_user__isnull=True).exclude(cat_user=request.user).order_by('-id')

        if not game_list:
            context_dict = dict()
            context_dict[constants.ERROR_MESSAGE_ID] = """No hay juegos disponibles. Necesitas amigos!"""
            return render(request, "mouse_cat/error.html", add_counter_to_context(request, context_dict))

        available_games = game_list
        context_dict = {'available_games': available_games}

        paginator = Paginator(available_games, 5)
        page = request.GET.get('page', 1)
        try:
            selected_page = paginator.page(page)
        except PageNotAnInteger:
            selected_page = paginator.page(1)
        except EmptyPage:
            selected_page = paginator.page(paginator.num_pages)
        context_dict['available_games'] = selected_page

        return render(request, "mouse_cat/select_join.html", add_counter_to_context(request, context_dict))
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def join_game_service(request, game_id=-1):
    if request.user.is_authenticated:
        game = Game.objects.get(id=game_id)

        if not game:
            # No consideramos esto un error por el que llamar al counter
            context_dict = dict()
            context_dict[constants.ERROR_MESSAGE_ID] = """No hay juegos disponibles. Necesitas amigos!"""
            return render(request, "mouse_cat/error.html", add_counter_to_context(request, context_dict))

        game.mouse_user = request.user
        game.full_clean()
        game.save()
        context_dict = {'game': game}

        return render(request, "mouse_cat/join_game.html", add_counter_to_context(request, context_dict))
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def select_view_service(request):
    if request.user.is_authenticated:
        game_list = Game.objects.filter(cat_user=request.user, status=3).union(
            Game.objects.filter(mouse_user=request.user, status=3),
            Game.objects.filter(cat_user=request.user, status=4),
            Game.objects.filter(mouse_user=request.user, status=4)
        ).order_by('id')
        if not game_list:
            context_dict = dict()
            context_dict[constants.ERROR_MESSAGE_ID] = """No hay juegos disponibles... Termina alguno y vuelve aquí!"""
            return render(request, "mouse_cat/error.html", add_counter_to_context(request, context_dict))

        ended = game_list
        context_dict = {'ended': ended}

        paginator = Paginator(ended, 5)
        page = request.GET.get('page', 1)
        try:
            selected_page = paginator.page(page)
        except PageNotAnInteger:
            selected_page = paginator.page(1)
        except EmptyPage:
            selected_page = paginator.page(paginator.num_pages)
        context_dict['ended'] = selected_page

        return render(request, "mouse_cat/select_view.html", add_counter_to_context(request, context_dict))
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def select_game_service(request, game_id=-1):
    if request.user.is_authenticated:
        if game_id is -1:
            context_dict = {}
            as_cat_list = Game.objects.filter(cat_user=request.user, status=GameStatus.ACTIVE).order_by('id')
            as_mouse_list = Game.objects.filter(mouse_user=request.user, status=GameStatus.ACTIVE).order_by('id')

            if as_mouse_list:
                paginator_mouse = Paginator(as_mouse_list, 5)
                page_mouse = request.GET.get('page_mouse', 1)
                try:
                    selected_mouse_page = paginator_mouse.page(page_mouse)
                except PageNotAnInteger:
                    selected_mouse_page = paginator_mouse.page(1)
                except EmptyPage:
                    selected_mouse_page = paginator_mouse.page(paginator_mouse.num_pages)
                context_dict['as_mouse'] = selected_mouse_page
            if as_cat_list:
                paginator_cat = Paginator(as_cat_list, 5)
                page_cat = request.GET.get('page_cat', 1)
                try:
                    selected_cat_page = paginator_cat.page(page_cat)
                except PageNotAnInteger:
                    selected_cat_page = paginator_cat.page(1)
                except EmptyPage:
                    selected_cat_page = paginator_cat.page(paginator_cat.num_pages)
                context_dict['as_cat'] = selected_cat_page

            return render(request, "mouse_cat/select_game.html", add_counter_to_context(request, context_dict))

        game = Game.objects.filter(id=game_id).first()
        if not game:
            return HttpResponseNotFound(constants.ERROR_NOT_FOUND)
        if game.status == GameStatus.CATWINNER or game.status == GameStatus.MOUSEWINNER:
            if game.cat_user == request.user or game.mouse_user == request.user:
                request.session['id_game_view'] = game_id

                return play_game_service(request)

            else:
                return HttpResponseNotFound(constants.ERROR_NOT_FOUND)
        else:
            if game.cat_user == request.user or game.mouse_user == request.user:
                request.session['game_id'] = game.id
                # Hacemos esto para evitar un problema de carga
                # con los urls de load_board
                return index(request)

            else:
                return HttpResponseNotFound(constants.ERROR_NOT_FOUND)
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def show_game_service(request):
    if request.user.is_authenticated:
        if 'game_id' not in request.session.keys():
            return errorHTTP(request, constants.MSG_ERROR_NO_GAME)

        game = Game.objects.get(id=request.session["game_id"])
        board = ([0] * (Game.MAX_CELL - Game.MIN_CELL + 1))
        for i in range(Game.MIN_CELL, Game.MAX_CELL + 1):
            '''Hecho a malas y rapidamente, pero tenia prisa'''
            if i not in Game.cell:
                board[i] = -2
        board[game.cat1] = board[game.cat2] = board[game.cat3] = board[game.cat4] = 1
        board[game.mouse] = -1

        context_dict = {'game': game, 'board': board, 'move_form': MoveForm()}
        return render(request, "mouse_cat/game.html", add_counter_to_context(request, context_dict))

    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def play_game_service(request):
    if request.user.is_authenticated:
        if 'id_game_view' not in request.session.keys():
            return errorHTTP(request, constants.MSG_ERROR_NO_GAME)
        game = Game.objects.get(id=request.session["id_game_view"])
        board = ([0] * (Game.MAX_CELL - Game.MIN_CELL + 1))
        for i in range(Game.MIN_CELL, Game.MAX_CELL + 1):
            '''Hecho a malas y rapidamente, pero tenia prisa'''
            if i not in Game.cell:
                board[i] = -2
        board[0] = board[2] = board[4] = board[6] = 1
        board[59] = -1

        context_dict = {'game': game, 'board': board}

        request.session['id_move_view'] = -1
        request.session['flag_move_view'] = 0
        return render(request, "mouse_cat/view_game.html", add_counter_to_context(request, context_dict))

    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def move_service(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if 'game_id' in request.session.keys():
                game_id = request.session['game_id']
                game = Game.objects.get(id=game_id)
                move_form = MoveForm(data=request.POST)
                if move_form.is_valid():
                    try:
                        move = Move(game=game, player=request.user, origin=move_form.data['origin'],
                                    target=move_form.data['target'])
                        move.save()
                    except ValidationError:
                        pass
                game = Game.objects.get(id=request.session["game_id"])
                board = ([0] * (Game.MAX_CELL - Game.MIN_CELL + 1))
                board[game.cat1] = board[game.cat2] = board[game.cat3] = board[game.cat4] = 1
                board[game.mouse] = -1
                for i in range(Game.MIN_CELL, Game.MAX_CELL + 1):
                    '''Hecho a malas y rapidamente, pero tenia prisa'''
                    if i not in Game.cell:
                        board[i] = -2
                move_form.add_error(None, constants.MSG_ERROR_INVALID_CELL)
                context_dict = {'game': game, 'board': board, 'move_form': move_form}
                return render(request, "mouse_cat/game.html", add_counter_to_context(request, context_dict))
        return HttpResponseNotFound('<h1>El método no era POST, no me uses así!</h1>')
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


def load_board(request, gameid):
    if request.user.is_authenticated:
        game = Game.objects.get(id=gameid)
        board = ([0] * (Game.MAX_CELL - Game.MIN_CELL + 1))
        for i in range(Game.MIN_CELL, Game.MAX_CELL + 1):
            '''Hecho a malas y rapidamente, pero tenia prisa'''
            if i not in Game.cell:
                board[i] = -2
        board[game.cat1] = board[game.cat2] = board[game.cat3] = board[game.cat4] = 1
        board[game.mouse] = -1
        context_dict = dict()
        context_dict['board'] = board
        context_dict['game'] = game
        context_dict['move_form'] = MoveForm()
        return render(request, "mouse_cat/board.html", context_dict)
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))


"""def get_moves_service(request):
    # No usamos esta version pero la planteamos
    if request.user.is_authenticated:
        if request.method == 'POST':
            inc_counter(request)
            return HttpResponseNotFound()

        id_game = request.session['id_game_view']

        if not Game.objects.filter(id=id_game).exists():
            inc_counter(request)
            return HttpResponseNotFound(constants.ERROR_NOT_FOUND)

        moves = []
        game = Game.objects.get(id=id_game)
        id_moves = game.moves.all().values_list('id')  # asumo que se guardan de menor a mayor (Este comentario se quita)
        min_move = id_moves[0]  # con esto sacamos el menor id
        max_move = id_moves[-1]  # con esto sacamos el mayor id

        for movimiento in game.moves.all().values_list('id', 'origin', 'target'):
            if movimiento[0] == min_move:
                moves.append({
                    'id': movimiento[0],
                    'origin': movimiento[1],
                    'target': movimiento[2],
                    'previous': 0,  # 0 indica que no hay movimientos anteriores ya que este es el primero
                    'next': 1  # 1 indica que hay movimientos posteriores

                })
            elif movimiento[0] == max_move:
                moves.append({
                    'id': movimiento[0],
                    'origin': movimiento[1],
                    'target': movimiento[2],
                    'previous': 1,  # 1 indica que hay movimientos anteriores ya que este es el primero
                    'next': 0  # 0 indica que no hay movimientos posteriores

                })
            else:
                moves.append({
                    'id': movimiento[0],
                    'origin': movimiento[1],
                    'target': movimiento[2],
                    'previous': 1,  # 1 indica que hay movimientos anteriores ya que este es el primero
                    'next': 1  # 1 indica que hay movimientos posteriores

                })
        return HttpResponse(json.dumps(moves), 200)

    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))"""


def get_moves_service(request, shift=-5, game_id=-1):
    if request.user.is_authenticated:
        if request.method == 'POST':
            inc_counter(request)
            return HttpResponseNotFound()

        if 'id_move_view' not in request.session.keys():
            request.session['id_move_view'] = -1
            request.session['flag_move_view'] = 0  # 2 movimiento previo next, 1 ,movimiento previo anterior

        if shift == 2:  # Con shift -1 dama error de direccionado en el URL
            shift = -1
        id_game = request.session['id_game_view']

        if not Game.objects.filter(id=id_game).exists():
            inc_counter(request)
            return HttpResponseNotFound(constants.ERROR_NOT_FOUND)

        id_move = request.session['id_move_view']

        if (request.session['flag_move_view'] == 1 or request.session['flag_move_view'] == 0) and shift == -1:
            id_move += shift  # esto sumara o restara uno a la variable
            request.session['flag_move_view'] = 1

        if (request.session['flag_move_view'] == 2 or request.session['flag_move_view'] == 0) and shift == 1:
            id_move += shift  # esto sumara o restara uno a la variable
            request.session['flag_move_view'] = 2

        moves = []
        game = Game.objects.get(id=id_game)
        id_moves = game.moves.all().values_list('id')
        min_move = id_moves[0][0]  # con esto sacamos el menor id
        max_move = id_moves[len(id_moves) - 1][0]  # con esto sacamos el mayor id
        # Error si no hay movimiento previo o siguiente

        if (request.session['id_move_view'] == -1 and shift == -1) or id_move >= len(id_moves):
            moves.append({
                'id': -5,
                'origin': -5,
                'target': -5,
                'previous': 1,  # 1 indica que hay movimientos anteriores ya que este es el primero
                'next': 1  # 1 indica que hay movimientos posteriores
            })
            return JsonResponse(moves[0])

        movimientos = game.moves.all().values_list('id', 'origin', 'target')
        if request.session['id_move_view'] == 0 and shift == -1:
            movimiento = movimientos[0]
            moves.append({
                'id': movimiento[0],
                'origin': movimiento[1],
                'target': movimiento[2],
                'previous': 1,  # 1 indica que hay movimientos anteriores ya que este es el primero
                'next': 1  # 1 indica que hay movimientos posteriores
            })
            request.session['id_move_view'] += shift
            return JsonResponse(moves[0])

        movimiento = movimientos[id_move]

        if movimiento[0] == min_move:
            moves.append({
                'id': movimiento[0],
                'origin': movimiento[1],
                'target': movimiento[2],
                'previous': 0,  # 0 indica que no hay movimientos anteriores ya que este es el primero
                'next': 1  # 1 indica que hay movimientos posteriores

            })
        elif movimiento[0] == max_move:
            moves.append({
                'id': movimiento[0],
                'origin': movimiento[1],
                'target': movimiento[2],
                'previous': 1,  # 1 indica que hay movimientos anteriores ya que este es el primero
                'next': 0  # 0 indica que no hay movimientos posteriores

            })
        else:
            moves.append({
                'id': movimiento[0],
                'origin': movimiento[1],
                'target': movimiento[2],
                'previous': 1,  # 1 indica que hay movimientos anteriores ya que este es el primero
                'next': 1  # 1 indica que hay movimientos posteriores

            })

        request.session['id_move_view'] += shift

        return JsonResponse(moves[0])

    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', add_counter_to_context(request, context_dict))
