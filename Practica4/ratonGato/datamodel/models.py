import datetime
from enum import Enum, IntEnum
from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from datamodel import constants


class GameStatus(IntEnum):
    CREATED = 1
    ACTIVE = 2
    MOUSEWINNER = 3
    CATWINNER = 4

    def __str__(self):
        if self == GameStatus.CREATED:
            return "Created"
        elif self == GameStatus.ACTIVE:
            return "Active"
        elif self == GameStatus.MOUSEWINNER:
            return "Mouse Won"
        elif self == GameStatus.CATWINNER:
            return "Cat Won"


class Game(models.Model):
    MIN_CELL = 0
    MAX_CELL = 63
    cell = (0, 2, 4, 6, 9, 11, 13, 15, 16, 18, 20, 22, 25, 27, 29, 31, 32, 34, 36, 38, 41, 43, 45, 47, 48, 50, 52, 54,
            57, 59, 61, 63)
    GameStatusEnum = [
        (GameStatus.CREATED, 'Created'),
        (GameStatus.ACTIVE, 'Active'),
        (GameStatus.MOUSEWINNER, 'Mouse Won'),
        (GameStatus.CATWINNER, 'Cat Won'),
    ]

    cat_user = models.ForeignKey(User, related_name='games_as_cat', null=False, on_delete=models.CASCADE)
    mouse_user = models.ForeignKey(User, related_name='games_as_mouse', null=True, on_delete=models.CASCADE, blank=True)
    cat1 = models.IntegerField(default=0)  # validators
    cat2 = models.IntegerField(default=2)
    cat3 = models.IntegerField(default=4)
    cat4 = models.IntegerField(default=6)
    mouse = models.IntegerField(default=59)
    cat_turn = models.BooleanField(default=True)
    status = models.IntegerField(choices=GameStatusEnum, default=GameStatus.CREATED)

    # def __unicode__(self):
    #   if self.mouseUser:
    #      return self.catUser.userName + " y " + self.mouseUser.userName
    # else:
    #    return self.catUser.userName
    def full_clean(self, *args, **kwargs):
        if (self.cat1 not in self.cell) or (self.cat2 not in self.cell) or (self.cat3 not in self.cell) or \
                (self.cat4 not in self.cell) or (self.mouse not in self.cell):
            raise ValidationError("Error al validar casilla")
        self.clean_fields()
        self.clean()
        self.validate_unique()

    def save(self, *args, **kwargs):
        if (self.mouse_user is not None) and (self.status == GameStatus.CREATED):
            self.status = GameStatus.ACTIVE
        if (self.cat1 not in self.cell) or (self.cat2 not in self.cell) or (self.cat3 not in self.cell) or \
                (self.cat4 not in self.cell) or (self.mouse not in self.cell):
            raise ValidationError("Invalid cell for a cat or the mouse|Gato o ratón en posición no válida")
        super().save(*args, **kwargs)

    def __str__(self):
        if self.status == GameStatus.CREATED:
            return "(" + str(self.id) + ", " + str(GameStatus(self.status)) + ")\tCat [X] " + self.cat_user.username +\
                   "(" + str(self.cat1) + ", " + str(self.cat2) + ", " + str(self.cat3) + ", " + str(self.cat4) + ")"
        elif self.status == GameStatus.ACTIVE:
            if self.cat_turn is True:
                return "(" + str(self.id) + ", " + str(GameStatus(self.status)) + ")\tCat [X] " + self.cat_user.username +\
                       "(" + str(self.cat1) + ", " + str(self.cat2) + ", " + str(self.cat3) + ", " + str(self.cat4) +\
                       ") --- Mouse [ ] " + self.mouse_user.username + "(" + str(self.mouse) + ")"
            else:
                return "(" + str(self.id) + ", " + str(GameStatus(self.status)) + ")\tCat [ ] " + self.cat_user.username + \
                       "(" + str(self.cat1) + ", " + str(self.cat2) + ", " + str(self.cat3) + ", " + str(self.cat4) + \
                       ") --- Mouse [X] " + self.mouse_user.username + "(" + str(self.mouse) + ")"
        else:
            if self.cat_turn is True:
                return "(" + str(self.id) + ", " + str(GameStatus(self.status)) + ")\tCat [X] " + self.cat_user.username +\
                       "(" + str(self.cat1) + ", " + str(self.cat2) + ", " + str(self.cat3) + ", " + str(self.cat4) +\
                       ") --- Mouse [ ] " + self.mouse_user.username + "(" + str(self.mouse) + ")"
            else:
                return "(" + str(self.id) + ", " + str(GameStatus(self.status)) + ")\tCat [ ] " + self.cat_user.username + \
                       "(" + str(self.cat1) + ", " + str(self.cat2) + ", " + str(self.cat3) + ", " + str(self.cat4) + \
                       ") --- Mouse [X] " + self.mouse_user.username + "(" + str(self.mouse) + ")"


class Move(models.Model):
    origin = models.IntegerField(default=-1)
    target = models.IntegerField(default=-1)
    game = models.ForeignKey(Game, null=False, on_delete=models.CASCADE, related_name='moves')
    player = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    date = models.DateField(auto_now=True, null=False)

    def save(self, *args, **kwargs):
        valido = False
        if self.game.status != GameStatus.ACTIVE:
            raise ValidationError(constants.MSG_ERROR_MOVE)

        if int(self.origin) in Game.cell and int(self.target) in Game.cell:
            if self.player == self.game.cat_user and self.game.cat_turn:
                if int(self.origin) == self.game.cat1 or int(self.origin) == self.game.cat2 or int(self.origin) == self.game.cat3 or int(self.origin) == self.game.cat4:
                    columna = int(self.origin) % 8
                    if columna == 0:
                        if int(self.target) == int(self.origin) + 9:
                            valido = True
                    elif columna == 7:
                        if int(self.target) == int(self.origin) + 7:
                            valido = True
                    else:
                        if int(self.target) == int(self.origin) + 7 or int(self.target) == int(self.origin) + 9:
                            valido = True

            elif self.player == self.game.mouse_user and not self.game.cat_turn:
                if int(self.origin) == self.game.mouse:
                    columna = int(self.origin) % 8
                    fila = int(self.origin) // 8
                    if columna == 0:
                        if fila == 8:
                            if int(self.target) == int(self.origin) - 7:
                                valido = True
                        else:
                            if int(self.target) == int(self.origin) - 7 or int(self.target) == int(self.origin) + 9:
                                valido = True
                    if columna == 7:
                        if fila == 8:
                            if int(self.target) == int(self.origin) - 9:
                                valido = True
                        else:
                            if int(self.target) == int(self.origin) - 9 or int(self.target) == int(self.origin) + 7:
                                valido = True
                    else:
                        if fila == 8:
                            if int(self.target) == int(self.origin) - 9 or int(self.target) == int(self.origin) - 7:
                                valido = True
                        else:
                            if int(self.target) == int(self.origin) - 9 or int(self.target) == int(self.origin) - 7 or int(self.target) == int(self.origin) + 7 or int(self.target) == int(self.origin) + 9:
                                valido = True

        if valido:
            if int(self.origin) == self.game.mouse:
                self.game.mouse = int(self.target)
            elif int(self.origin) == self.game.cat1:
                self.game.cat1 = int(self.target)
            elif int(self.origin) == self.game.cat2:
                self.game.cat2 = int(self.target)
            elif int(self.origin) == self.game.cat3:
                self.game.cat3 = int(self.target)
            elif int(self.origin) == self.game.cat4:
                self.game.cat4 = int(self.target)

            # Condicion de victoria
            if self.game.cat1 == self.game.mouse or self.game.cat2 == self.game.mouse or self.game.cat3 == self.game.mouse or self.game.cat4 == self.game.mouse:
                self.game.status = GameStatus.CATWINNER
            elif self.game.mouse == 0 or self.game.mouse == 2 or self.game.mouse == 4 or self.game.mouse == 6:
                self.game.status = GameStatus.MOUSEWINNER

            self.game.cat_turn = not self.game.cat_turn
            self.date = datetime.datetime.now()
            super().save(*args, **kwargs)
            self.game.save()
        else:
            raise ValidationError(constants.MSG_ERROR_MOVE)

    def __unicode__(self):
        if self.game.mouseUser:
            return self.game.catUser.userName + " and " + self.game.mouseUser.userName
        else:
            return self.game.catUser.userName


class CounterManager(models.Manager):
    counter = None

    def inc(self, *args, **kwargs):
        try:
            counter = self.get(pk=0)
        except:
            self.__createCounter(self)
            counter = self.get(pk=0)
        counter.value += 1
        super(Counter, counter).save(*args, **kwargs)
        return counter.value

    def get_current_value(self):
        try:
            counter = self.get(pk=0)
        except:
            self.__createCounter(self)
            counter = self.get(pk=0)
        return counter.value

    def __createCounter(self, *args, **kwargs):
        counter = Counter(0, 0)
        super(Counter, counter).save(*args, **kwargs)


class Counter(models.Model):
    value = models.IntegerField(default=0)
    objects = CounterManager()

    def save(self, *args, **kwargs):
        raise ValidationError("Insert not allowed|Inseción no permitida")


''' Comentado porque quita funcionalidad 
class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, default="user")
    games_as_mouse = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='games_as_mouse',
                                       null=True, blank=True)
    games_as_cat = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='games_as_cat',
                                     null=True, blank=True)

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=User)
    def create_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(username=instance)

    @receiver(post_save, sender=User)
    def save_profile(sender, instance, **kwargs):
        instance.userprofile.save()'''
