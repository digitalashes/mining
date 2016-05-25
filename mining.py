# -*- coding: utf-8 -*-
# ! python3

# ======================================================================================================================
# Author: Half-Life
# Description: Скрипт на добычу руды по кочкам. Не обкапывает скалы!
#   Чар должен иметь 100 LRC и около 65-70 тинкера.
#   Делает лопаты.
#   Реколится магией или чивой.
#   Написан под RunUO.
#   Тестировался на шарде UOAwakening.
# UOStealthClientVersion: 7.3.1
# Warning! Будьте бдительны! - Администрация многих игровых серверов
# враждебно относится к использованию стелс клиента на своих серверах.
# Заподозрив вас в использовании стелс клиента и других неправославных программ
# они начинают сатанеть и в порыве слепой ярости могут попасть по вам Банхаммером
# ======================================================================================================================
from datetime import datetime, timedelta

from stealthapi import *

# ======================================================================================================================
# CONSTANTS
# ======================================================================================================================

INGOTS_STORAGE = 0x4010303A  # ID Контейнера в который скидывать металл и камни.
INGOTS_TYPE = 0x1BF2  # Тип металла (инготов).

USE_TRASH = True  # Использовать треш. Если не надо установить False
TRASH = 0x40603E6E  # ID Мусорки

HOME_RUNE_BOOK = 0x40258A6E  # ID Рунабуки с рункой в дом
RUNE_BOOK_GUMP_ID = 0x554B87F3  # ID Гампа рунабуки.
HOME_RUNE = 1  # Номер рунки домой. Отсчёт начинается с 1.
RUNE_BOOK_SHIFT = 7  # Рекол. 5 - магия, 7 - чива.
RUNE_BOOKS = [0x40258C7E, 0x40258C14]  # Рунабуки с рунками к кочкам.
ORE_TYPES = [0x19B9]  # Типы руды.
GEM_TYPES = [0x3192, 0x3193, 0x3194, 0x3195, 0x3197, 0x3198, 0x5732]  # Типы камней.
RESOURCES = ORE_TYPES + GEM_TYPES
TRASH_ITEMS = [0x0F27]  # Типы мусора.

MINING_TYPE = 0x0F39  # Тип лопаты.
TINKER_TYPE = 0x1EB8  # Тип тинкер тулзы.

TK_NUM_FIRST = '15'  # Номер кнопки 'Tools' в тинкер меню.
TK_NUM_SECOND = '23'  # Номер кнопки 'Tinker's Tools' в тинкер меню.
TK_CRAFT_NUM_SECOND = '72'  # Номер кнопки 'Shovel' в тинкер меню.
TOOLS_GUMP_ID = 0x38920ABD  # ID Гампа тулзы.

IRON_COLOR = 0x0000  # Цвет обычного металла(инготов).
IRON_COUNT = 40  # Минимум металла для крафта лопат

WAIT_TIME = 500  # Время минимальной задержки. Лучше не менять.
WAIT_LAG_TIME = 10000  # Время кторое будет выжидаться при лаге. Лучше не менять.

# ======================================================================================================================
# Variables
# ======================================================================================================================

current_book, current_rune = 0, 0


# ======================================================================================================================
# Utils
# ======================================================================================================================

def wait_lag(wait_time=WAIT_TIME, lag_time=WAIT_LAG_TIME):
    Wait(wait_time)
    CheckLag(lag_time)
    return


def close_gumps():
    while IsGump():
        if not Connected():
            return False
        if not IsGumpCanBeClosed(GetGumpsCount() - 1):
            WaitGump('0')
        else:
            CloseSimpleGump(GetGumpsCount() - 1)
    return True


# ======================================================================================================================
# Last Container
# ======================================================================================================================

class LastContainer(object):
    DELAY = 10

    def __eq__(self, other):
        if self.serial == other:
            return self.check_time(self.DELAY)
        return False

    def __call__(self, serial, graphic):
        self.graphic = graphic
        self.serial = serial
        self.last_time = datetime.datetime.now()

    def __init__(self):
        self.serial = 0
        self.last_time = datetime.datetime.now()

    def check_time(self, seconds):
        delta = timedelta(seconds=seconds)
        if datetime.datetime.now() <= delta + self.last_time:
            return True
        return False


# ======================================================================================================================
# Check States
# ======================================================================================================================

def check_connection():
    if not Connected():
        AddToSystemJournal('Нет коннекта.')
        while not Connected():
            AddToSystemJournal('Пытаюсь законектиться...')
            Wait(5000)
        AddToSystemJournal('Есть коннект.')
        close_gumps()
    return


def check_dead():
    if Dead():
        AddToSystemJournal('Мне очень жаль. Вы умерли.')
        AddToSystemJournal('Рунабука {0}'.format(GetToolTip(current_book).split('|')[-1]))
        AddToSystemJournal('Рунка № # {0}'.format(current_rune))
        quit('You are Dead.')
    return


def check_states():
    check_connection()
    check_dead()
    return


# ======================================================================================================================
# Check HP
# ======================================================================================================================

def check_hp():
    if GetHP(Self()) == MaxLife():
        return
    SetAlarm()
    AddToSystemJournal('Вас кто-то атакует.')
    SendTextToUO('Guards')
    while Life() != MaxLife():
        check_states()
        Cast('Close Wounds')
        WaitTargetSelf()
        wait_lag()
    return


# ======================================================================================================================
# Check Ingots
# ======================================================================================================================

def check_ingots():
    FindTypeEx(INGOTS_TYPE, IRON_COLOR, Backpack(), False)
    count_in_pack = FindFullQuantity()
    if count_in_pack < IRON_COUNT:
        AddToSystemJournal('Проверяю металл.')
        last_container = LastContainer()
        SetEventProc('evDrawContainer', last_container)
        while True:
            check_states()
            UseObject(INGOTS_STORAGE)
            wait_lag(WAIT_TIME * 2)
            if last_container == INGOTS_STORAGE:
                SetEventProc('evDrawContainer', None)
                break
        FindTypeEx(INGOTS_TYPE, IRON_COLOR, INGOTS_STORAGE, False)
        count_in_box = FindFullQuantity()
        wait_lag()
        AddToSystemJournal('Металла осталось: {0}'.format(count_in_box))
        if count_in_box < IRON_COUNT:
            AddToSystemJournal('Закончился металл. Стоп.')
            quit('Закончился металл.')
        Grab(FindItem(), IRON_COUNT - count_in_pack)
    return


# ======================================================================================================================
# Unload
# ======================================================================================================================

def unload(items, container, msg):
    AddToSystemJournal('Разгружаю {0}'.format(msg))
    for item in items:
        while FindType(item, Backpack()) > 1:
            check_states()
            MoveItem(FindItem(), GetQuantity(FindItem()), container, 0, 0, 0)
            wait_lag()
    AddToSystemJournal('Разгрузились.')
    return


# ======================================================================================================================
# Drop Ore
# ======================================================================================================================

def drop_ore():
    AddToSystemJournal('Сбрасываю баласт...')
    counter = 0
    while True:
        counter += 1
        FindTypeEx(ORE_TYPES[0], 0, Backpack(), False)
        if Weight() < MaxWeight():
            break
        wait_lag()
        if counter == 1:
            Drop(FindItem(), 1, GetX(Self()) - 1, GetY(Self()), GetZ(Self()))
            continue
        if counter == 2:
            Drop(FindItem(), 1, GetX(Self()) + 1, GetY(Self()), GetZ(Self()))
            continue
        if counter == 3:
            Drop(FindItem(), 1, GetX(Self()), GetY(Self()) - 1, GetZ(Self()))
            continue
        if counter == 4:
            Drop(FindItem(), 1, GetX(Self()), GetY(Self()) + 1, GetZ(Self()))
            continue
        elif counter == 5:
            Drop(FindItem(), 1, GetX(Self()) + 1, GetY(Self()) + 1, GetZ(Self()))
            continue
        elif counter == 6:
            Drop(FindItem(), 1, GetX(Self()) - 1, GetY(Self()) - 1, GetZ(Self()))
            continue
        elif counter == 7:
            Drop(FindItem(), 1, GetX(Self()) + 1, GetY(Self()) - 1, GetZ(Self()))
            continue
        elif counter == 8:
            Drop(FindItem(), 1, GetX(Self()) - 1, GetY(Self()) + 1, GetZ(Self()))
            continue
        else:
            break
    return


# ======================================================================================================================
# Recalling
# ======================================================================================================================

def degrees_to_coordinate(coordinate, center, size):
    result = ((coordinate['deg'] * 100) + ((coordinate['min'] * 10) // 6))
    if coordinate['dir'] == 'N' or coordinate['dir'] == 'W':
        result = 36000 - result
    result = int(round((center + (result * size) / 36000) % size, 0))
    return result


def get_coordinates(destination):
    position = {'x': 0, 'y': 0}
    if GetGumpID(GetGumpsCount() - 1) != RUNE_BOOK_GUMP_ID:
        return position
    gump_info = GetGumpInfo(GetGumpsCount() - 1)
    i = destination + destination
    latitude_longitude = gump_info['GumpText'][i:i + 2]
    latitude_text_id = latitude_longitude[0]['TextID']
    longitude_text_id = latitude_longitude[1]['TextID']
    coordinates = gump_info['Text'][latitude_text_id] + ' ' + gump_info['Text'][longitude_text_id]
    coordinates = coordinates.replace('\'', ' ').replace('°', '').split(' ')
    latitude = {
        'deg': int(coordinates[0]),
        'min': int(coordinates[1]),
        'dir': coordinates[2],
    }
    longitude = {
        'deg': int(coordinates[3]),
        'min': int(coordinates[4]),
        'dir': coordinates[5],
    }
    position['x'] = degrees_to_coordinate(longitude, 1323, 5120)
    position['y'] = degrees_to_coordinate(latitude, 1624, 4096)
    return position


def recall_to(rune_book, destination):
    destination_position = {}
    if rune_book == HOME_RUNE_BOOK:
        AddToSystemJournal('Пытаюсь среколиться домой...')
    else:
        rune_book_name = GetToolTip(rune_book).split('|')[-1]
        AddToSystemJournal('Пытаюсь среколиться... RuneBook - {0} Rune № #{1}'.format(rune_book_name, current_rune))
    while True:
        check_states()
        close_gumps()
        self_position = {'x': GetX(Self()), 'y': GetY(Self())}
        if self_position != destination_position:
            while GetGumpID(GetGumpsCount() - 1) != RUNE_BOOK_GUMP_ID:
                UseObject(rune_book)
                wait_lag()
                destination_position = get_coordinates(destination - 1)
            WaitGump(str(destination * 6 + RUNE_BOOK_SHIFT - 6))
            wait_lag(WAIT_TIME * 4)
        else:
            close_gumps()
            break
        if InJournal('Thou art too encumbered to move.') > 0:
            ClearJournal()
            AddToSystemJournal('Перегруз!')
            drop_ore()
    AddToSystemJournal('Cреколились.')
    return True


# ======================================================================================================================
# Check Weight
# ======================================================================================================================

def check_weight():
    if MaxWeight() > Weight() + 60:
        return
    check_connection()
    recall_to(HOME_RUNE_BOOK, HOME_RUNE)
    unload(RESOURCES, INGOTS_STORAGE, msg='ресурсы')
    if USE_TRASH:
        unload(TRASH_ITEMS, TRASH, msg='мусор')
    check_ingots()
    recall_to(current_book, current_rune)
    return


# ======================================================================================================================
# Event Create Tools
# ======================================================================================================================

def event_create_tools(num_f, num_s, name):
    WaitGump(num_f)
    WaitGump(num_s)
    AddToSystemJournal(name)
    wait_lag(WAIT_TIME * 2)
    return


# ======================================================================================================================
# Check Tools
# ======================================================================================================================

def check_tool(check_type, count=1):
    check_states()
    CheckLag(WAIT_LAG_TIME)
    return CountEx(check_type, 0, Backpack()) > count - 1


# ======================================================================================================================
# Create Tools
# ======================================================================================================================

def create_tk_tools():
    SetEventProc('evIncomingGump', event_create_tools(TK_NUM_FIRST, TK_NUM_SECOND, 'Create tinker tools'))
    while not check_tool(TINKER_TYPE, 2):
        check_states()
        if not IsGump():
            UseType(TINKER_TYPE, 0)
    SetEventProc('evIncomingGump', None)
    return


def create_craft_tools():
    if not check_tool(TINKER_TYPE, 2):
        create_tk_tools()
    SetEventProc('evIncomingGump', event_create_tools(TK_NUM_FIRST, TK_CRAFT_NUM_SECOND, 'Create mining tools'))
    if not IsGump():
        UseType(TINKER_TYPE, 0)
    SetEventProc('evIncomingGump', None)
    return check_tool(MINING_TYPE, 1)


# ======================================================================================================================
# Mine
# ======================================================================================================================

def mine():
    AddToSystemJournal('Копаю.')
    ClearJournal()
    while InJournal('t mine there|is too far away|cannot be seen|is no metal here to mine') < 0:
        check_states()
        check_weight()
        check_hp()
        if TargetPresent():
            CancelTarget()
        while not check_tool(MINING_TYPE, 1):
            create_craft_tools()
        close_gumps()
        UseType(MINING_TYPE, 0)
        self_x = GetX(Self())
        self_y = GetY(Self())
        self_z = GetZ(Self())
        WaitTargetTile(0, self_x, self_y, self_z)
        wait_lag(WAIT_TIME, 0)
    return AddToSystemJournal('Здесь металла нет.')


# ======================================================================================================================
# Set Mine Point
# ======================================================================================================================

def mine_point():
    global current_book, current_rune
    for current_book in RUNE_BOOKS:
        for current_rune in range(1, 17):
            check_states()
            if recall_to(current_book, current_rune):
                wait_lag()
                mine()
    return


# ======================================================================================================================
# Main
# ======================================================================================================================

if __name__ == '__main__':
    # ==================================================================================================================
    # Start Script
    # ==================================================================================================================
    ClearJournal()
    ClearSystemJournal()
    AddToSystemJournal('Стартуем')
    SetARStatus(True)
    check_states()
    AddToSystemJournal('Закрываем гампы')
    close_gumps()
    AddToSystemJournal('Гампы закрыты')
    recall_to(HOME_RUNE_BOOK, HOME_RUNE)
    unload(RESOURCES, INGOTS_STORAGE, msg='ресурсы')
    if USE_TRASH:
        unload(TRASH_ITEMS, TRASH, msg='мусор')
    check_ingots()
    while True:
        mine_point()

# ======================================================================================================================
# End Script
# ======================================================================================================================
