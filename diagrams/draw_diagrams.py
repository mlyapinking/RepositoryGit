#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Аккуратные ER и Use Case: связи PK→FK, ортогональные линии."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUT_ER = '/workspace/diagrams/05_er_diagram.png'
OUT_UC = '/workspace/diagrams/01_use_case.png'

BG = '#1e1e1e'
GRID = '#3a3a3a'
BOX_FILL = '#2b2b2b'
BOX_EDGE = '#ffffff'
TEXT = '#ffffff'
LINE = '#ffffff'
ROW_H = 0.36
HEADER_H = 0.5


def draw_grid(ax, xlim, ylim, step=0.5):
    ax.set_facecolor(BG)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('equal')
    ax.axis('off')
    for x in np.arange(xlim[0], xlim[1] + step, step):
        ax.axvline(x, color=GRID, linewidth=0.35, zorder=0)
    for y in np.arange(ylim[0], ylim[1] + step, step):
        ax.axhline(y, color=GRID, linewidth=0.35, zorder=0)


def er_table(ax, x, y, w, title, pk_name, attrs, fks):
    """Таблица с точками привязки PK (справа) и каждого FK (слева)."""
    rows = 1 + len(attrs) + len(fks)  # PK + attrs + FKs
    h = HEADER_H + rows * ROW_H
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle='square,pad=0.01',
        facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.4, zorder=2))

    # заголовок
    ty = y + h - HEADER_H
    ax.plot([x, x + w], [ty, ty], color=BOX_EDGE, lw=0.9, zorder=3)
    ax.text(x + w / 2, ty + HEADER_H / 2, title, ha='center', va='center',
            fontsize=10.5, color=TEXT, fontweight='bold', zorder=5)

    cy = ty
    pk_point = None

    # PK
    cy -= ROW_H
    ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.7, zorder=3)
    ax.text(x + 0.1, cy + ROW_H / 2, 'PK', ha='left', va='center', fontsize=7.5, color='#bbb', zorder=5)
    ax.text(x + 0.48, cy + ROW_H / 2, pk_name, ha='left', va='center', fontsize=8.5, color=TEXT, zorder=5)
    pk_point = (x + w, cy + ROW_H / 2)

    # атрибуты
    for attr in attrs:
        cy -= ROW_H
        ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.5, zorder=3)
        ax.text(x + 0.15, cy + ROW_H / 2, attr, ha='left', va='center', fontsize=8.5, color=TEXT, zorder=5)

    # FK
    fk_points = {}
    for fk in fks:
        cy -= ROW_H
        ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.7, zorder=3)
        ax.text(x + 0.1, cy + ROW_H / 2, 'FK', ha='left', va='center', fontsize=7.5, color='#bbb', zorder=5)
        ax.text(x + 0.48, cy + ROW_H / 2, fk, ha='left', va='center', fontsize=8.5, color=TEXT, zorder=5)
        fk_points[fk] = (x, cy + ROW_H / 2)

    return {
        'x': x, 'y': y, 'w': w, 'h': h,
        'pk': pk_point,
        'fk': fk_points,
        'right': x + w,
        'left': x,
        'top': y + h,
        'bottom': y,
        'cx': x + w / 2,
    }


def tick_one(ax, point, direction='right'):
    """Черточка «один» у PK."""
    x, y = point
    d = 0.14 if direction == 'right' else -0.14
    ax.plot([x, x + d], [y - 0.1, y - 0.1], color=LINE, lw=1.3, zorder=4)
    ax.plot([x, x + d], [y + 0.1, y + 0.1], color=LINE, lw=1.3, zorder=4)


def crow_many(ax, point, direction='left'):
    """Вилка «много» у FK."""
    x, y = point
    if direction == 'left':
        ax.plot([x, x - 0.12], [y, y + 0.1], color=LINE, lw=1.2, zorder=4)
        ax.plot([x, x - 0.12], [y, y], color=LINE, lw=1.2, zorder=4)
        ax.plot([x, x - 0.12], [y, y - 0.1], color=LINE, lw=1.2, zorder=4)
    else:
        ax.plot([x, x + 0.12], [y, y + 0.1], color=LINE, lw=1.2, zorder=4)
        ax.plot([x, x + 0.12], [y, y], color=LINE, lw=1.2, zorder=4)
        ax.plot([x, x + 0.12], [y, y - 0.1], color=LINE, lw=1.2, zorder=4)


def connect_pk_fk(ax, pk_point, fk_point, route='auto'):
    """
    Связь 1→M: от PK (родитель) к FK (потомок).
    Ортогональная линия, видно начало и конец у ключей.
    """
    x1, y1 = pk_point
    x2, y2 = fk_point

    if route == 'auto':
        route = 'hvh' if abs(y1 - y2) > 0.3 else 'h'

    if route == 'h':
        # горизонталь напрямую
        ax.plot([x1, x2], [y1, y2], color=LINE, lw=1.15, zorder=1, solid_capstyle='round')
    elif route == 'hvh':
        mid = (x1 + x2) / 2
        ax.plot([x1, mid], [y1, y1], color=LINE, lw=1.15, zorder=1)
        ax.plot([mid, mid], [y1, y2], color=LINE, lw=1.15, zorder=1)
        ax.plot([mid, x2], [y2, y2], color=LINE, lw=1.15, zorder=1)
    elif route == 'vhv':
        mid = (y1 + y2) / 2
        ax.plot([x1, x1], [y1, mid], color=LINE, lw=1.15, zorder=1)
        ax.plot([x1, x2], [mid, mid], color=LINE, lw=1.15, zorder=1)
        ax.plot([x2, x2], [mid, y2], color=LINE, lw=1.15, zorder=1)

    tick_one(ax, pk_point, 'right' if x2 > x1 else 'left')
    crow_many(ax, fk_point, 'left' if x2 > x1 else 'right')


def build_er():
    fig, ax = plt.subplots(figsize=(16, 11), dpi=160)
    draw_grid(ax, (0, 16), (0, 11))

    W = 2.55

    # --- размещение с запасом между таблицами ---
    auto = er_table(ax, 1.0, 7.2, W, 'Автомобили', 'КодАвтомобиля',
                    ['Наименование', 'ГосНомер', 'Марка'], [])
    tip = er_table(ax, 1.0, 4.5, W, 'ТипКлиента', 'КодТипа', ['Значения'], [])
    kl = er_table(ax, 1.0, 1.2, W, 'Клиенты', 'КодКлиента',
                  ['наименование', 'Адрес'], ['ТипКлиента'])
    sotr = er_table(ax, 6.2, 1.0, W, 'Сотрудники', 'КодСотрудника',
                    ['Наименование', 'Дата', 'Телефон'], [])
    punkt = er_table(ax, 11.5, 1.0, W, 'ПунктВыдачи', 'КодПункта',
                     ['Наименование'], ['Сотрудник', 'Автомобиль'])
    dog = er_table(ax, 11.2, 4.3, W + 0.35, 'ДоговорАренды', 'КодДоговора',
                   ['Дата', 'КолСуток', 'Номер'],
                   ['Автомобиль', 'ПунктВыдачи', 'Клиент'])
    stat = er_table(ax, 11.2, 7.5, W + 0.35, 'СтатусАвтопарка', 'КодСтатуса',
                    ['статус', 'период'], ['автомобиль', 'Договор'])

    # --- связи строго PK → FK ---
    connect_pk_fk(ax, tip['pk'], kl['fk']['ТипКлиента'], 'h')

    connect_pk_fk(ax, kl['pk'], dog['fk']['Клиент'], 'hvh')

    connect_pk_fk(ax, auto['pk'], dog['fk']['Автомобиль'], 'hvh')

    connect_pk_fk(ax, auto['pk'], punkt['fk']['Автомобиль'], 'hvh')

    connect_pk_fk(ax, auto['pk'], stat['fk']['автомобиль'], 'h')

    connect_pk_fk(ax, sotr['pk'], punkt['fk']['Сотрудник'], 'h')

    connect_pk_fk(ax, punkt['pk'], dog['fk']['ПунктВыдачи'], 'hvh')

    connect_pk_fk(ax, dog['pk'], stat['fk']['Договор'], 'hvh')

    fig.savefig(OUT_ER, facecolor=BG, bbox_inches='tight', pad_inches=0.12)
    plt.close(fig)
    print('ER OK')


# ---------- USE CASE ----------

def uc_ellipse(ax, cx, cy, text, w=1.22, h=0.72, fs=7.2):
    ax.add_patch(mpatches.Ellipse(
        (cx, cy), w, h, facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.1, zorder=3))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs, color=TEXT, zorder=4)
    return {'cx': cx, 'cy': cy, 'w': w, 'h': h,
            'left': cx - w/2, 'right': cx + w/2, 'top': cy + h/2, 'bottom': cy - h/2}


def uc_actor(ax, x, y, label, side='left'):
    """Актор: stick figure."""
    r = 0.18
    ax.add_patch(plt.Circle((x, y), r, fill=False, edgecolor=LINE, lw=1.1, zorder=5))
    foot_y = y - 0.85
    ax.plot([x, x], [y - r, y - 0.5], color=LINE, lw=1.1, zorder=5)
    ax.plot([x - 0.22, x + 0.22], [y - 0.32, y - 0.32], color=LINE, lw=1.1, zorder=5)
    ax.plot([x, x - 0.18], [y - 0.5, foot_y], color=LINE, lw=1.1, zorder=5)
    ax.plot([x, x + 0.18], [y - 0.5, foot_y], color=LINE, lw=1.1, zorder=5)
    ax.text(x, foot_y - 0.22, label, ha='center', va='top', fontsize=8.5, color=TEXT, zorder=5)
    if side == 'left':
        return {'anchor': (x + 0.25, y - 0.35), 'side': 'left'}
    return {'anchor': (x - 0.25, y - 0.35), 'side': 'right'}


def link_actor_uc(ax, actor, uc, dashed=False):
    """Аккуратная связь: актор → край овала (ближайшая точка)."""
    ax0, ay0 = actor['anchor']
    cx, cy = uc['cx'], uc['cy']
    side = actor['side']

    if side == 'left':
        tx = uc['left']
        ty = max(uc['bottom'], min(uc['top'], ay0))
        mid_x = (ax0 + tx) / 2
        ls = '--' if dashed else '-'
        ax.plot([ax0, mid_x], [ay0, ay0], color=LINE, lw=0.95, ls=ls, zorder=1)
        ax.plot([mid_x, mid_x], [ay0, ty], color=LINE, lw=0.95, ls=ls, zorder=1)
        ax.plot([mid_x, tx], [ty, ty], color=LINE, lw=0.95, ls=ls, zorder=1)
    else:
        tx = uc['right']
        ty = max(uc['bottom'], min(uc['top'], ay0))
        mid_x = (ax0 + tx) / 2
        ls = '--' if dashed else '-'
        ax.plot([ax0, mid_x], [ay0, ay0], color=LINE, lw=0.95, ls=ls, zorder=1)
        ax.plot([mid_x, mid_x], [ay0, ty], color=LINE, lw=0.95, ls=ls, zorder=1)
        ax.plot([mid_x, tx], [ty, ty], color=LINE, lw=0.95, ls=ls, zorder=1)


def build_use_case():
    fig, ax = plt.subplots(figsize=(9, 9), dpi=180)
    draw_grid(ax, (0, 9), (0, 9))

    # рамка системы
    bx, by, bw, bh = 2.0, 1.5, 5.0, 5.5
    ax.add_patch(FancyBboxPatch(
        (bx, by), bw, bh, boxstyle='square,pad=0.02',
        facecolor='none', edgecolor=BOX_EDGE, linewidth=1.8, zorder=2))
    ax.text(bx + bw / 2, by + bh + 0.28, 'ИС учёта аренды автомобилей',
            ha='center', va='bottom', fontsize=10, color=TEXT, fontweight='bold')

    # 3 ряда × 3 овала — ровная сетка
    xs = [2.85, 4.5, 6.15]
    ys = [5.6, 4.1, 2.6]
    labels = [
        ['Управление\nпользователями', 'Управление\nправами', 'Ведение\nсправочников'],
        ['Регистрация\nклиента', 'Оформление\nдоговора\nаренды', 'Закрытие\nаренды'],
        ['Учёт пробега\nи доплат', 'Отчёт\n«Автопарк»', 'Отчёт\n«Доходы»'],
    ]
    ucs = []
    for row, y in enumerate(ys):
        row_uc = []
        for col, x in enumerate(xs):
            row_uc.append(uc_ellipse(ax, x, y, labels[row][col]))
        ucs.append(row_uc)

    admin = uc_actor(ax, 0.75, 6.8, 'Администратор', 'left')
    mgr = uc_actor(ax, 0.75, 4.1, 'Менеджер', 'left')
    director = uc_actor(ax, 8.25, 4.1, 'Директор', 'right')
    client = uc_actor(ax, 8.25, 2.6, 'Клиент', 'right')

    for uc in ucs[0]:
        link_actor_uc(ax, admin, uc)
    for uc in ucs[1]:
        link_actor_uc(ax, mgr, uc)
    for uc in ucs[2][:1]:
        link_actor_uc(ax, mgr, uc)
    for uc in ucs[2][1:]:
        link_actor_uc(ax, director, uc)
    link_actor_uc(ax, client, ucs[1][1], dashed=True)

    fig.savefig(OUT_UC, facecolor=BG, bbox_inches='tight', pad_inches=0.08)
    plt.close(fig)
    print('UC OK')


if __name__ == '__main__':
    build_er()
    build_use_case()
