from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as mylogout
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render

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
    context_dict = {}
    context_dict[constants.ERROR_MESSAGE_ID] = exception
    return render(request, "mouse_cat/error.html", context_dict)


def index(request):
    return render(request, "mouse_cat/index.html")


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
        return render(request, 'mouse_cat/login.html', context_dict)
    else:
        user_form = LogInForm()
        context_dict = {'user_form': user_form}
        return render(request, 'mouse_cat/login.html', context_dict)


@login_required
def logout_service(request):
    user = request.user
    mylogout(request)
    request.session['counter'] = 0
    context_dict = {'user': user}
    return render(request, 'mouse_cat/logout.html', context_dict)


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
                    return render(request, "mouse_cat/index.html")
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

    return render(request, 'mouse_cat/signup.html', context_dict)


def counter_service(request):
    if 'counter' in request.session:
        request.session['counter'] += 1
    else:
        request.session['counter'] = 1

    counter_global = Counter.objects.inc()
    context_dict = {'counter_session': request.session['counter'], 'counter_global': counter_global}
    return render(request, 'mouse_cat/counter.html', context_dict)


def create_game_service(request):
    if request.user.is_authenticated:
        game = Game(cat_user=request.user)
        game.save()
        return render(request, "mouse_cat/new_game.html", {'game': game})
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', context_dict)


def join_game_service(request):
    if request.user.is_authenticated:
        game_list = Game.objects.filter(mouse_user__isnull=True).exclude(cat_user=request.user).order_by('-id')

        if not game_list:
            context_dict = {}
            context_dict[constants.ERROR_MESSAGE_ID] = """No available games|No hay juegos disponibles"""
            return render(request, "mouse_cat/join_game.html", context_dict)
        game = game_list.first()
        game.mouse_user = request.user
        game.save()
        context_dict = {'game': game}

        return render(request, "mouse_cat/join_game.html", context_dict)
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', context_dict)


def select_game_service(request, game_id=-1):
    if request.user.is_authenticated:
        if game_id is -1:
            context_dict = {}
            as_cat = Game.objects.filter(cat_user=request.user, status=GameStatus.ACTIVE)
            as_mouse = Game.objects.filter(mouse_user=request.user, status=GameStatus.ACTIVE)
            if as_mouse:
                context_dict['as_mouse'] = as_mouse
            if as_cat:
                context_dict['as_cat'] = as_cat
            return render(request, "mouse_cat/select_game.html", context_dict)

        game = Game.objects.filter(id=game_id).first()
        if not game:
            return HttpResponseNotFound(constants.ERROR_NOT_FOUND)
        if game.status != GameStatus.ACTIVE:
            return HttpResponseNotFound(constants.ERROR_NOT_FOUND)
        else:
            if game.cat_user == request.user or game.mouse_user == request.user:
                request.session['game_id'] = game.id
                return show_game_service(request)

            else:
                return HttpResponseNotFound(constants.ERROR_NOT_FOUND)
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', context_dict)


def show_game_service(request):
    if request.user.is_authenticated:
        game = Game.objects.get(id=request.session["game_id"])
        board = ([0] * (Game.MAX_CELL - Game.MIN_CELL + 1))
        board[game.cat1] = board[game.cat2] = board[game.cat3] = board[game.cat4] = 1
        board[game.mouse] = -1

        context_dict = {'game': game, 'board': board, 'move_form': MoveForm()}
        return render(request, "mouse_cat/game.html", context_dict)

    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', context_dict)


def move_service(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            if 'game_id' in request.session.keys():
                game_id = request.session['game_id']
                game = Game.objects.get(id=game_id)
                move_form = MoveForm(data=request.POST)

                if move_form.is_valid():
                    move = Move(game=game, player=request.user, origin=move_form.data['origin'], target=move_form.data['target'])
                    move.save()
                return show_game_service(request)

        return HttpResponseNotFound('<h1>Page Not Found</h1>')
    user_form = LogInForm()
    context_dict = {'user_form': user_form}
    return render(request, 'mouse_cat/login.html', context_dict)
