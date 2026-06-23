#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Аккуратные ER и Use Case: связи строго PK→FK, ортогональные линии."""

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
ROW_H = 0.34
HEADER_H = 0.48


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
    rows = 1 + len(attrs) + len(fks)
    h = HEADER_H + rows * ROW_H
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle='square,pad=0.01',
        facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.3, zorder=2))

    ty = y + h - HEADER_H
    ax.plot([x, x + w], [ty, ty], color=BOX_EDGE, lw=0.9, zorder=3)
    ax.text(x + w / 2, ty + HEADER_H / 2, title, ha='center', va='center',
            fontsize=10, color=TEXT, fontweight='bold', zorder=5)

    cy = ty
    cy -= ROW_H
    ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.7, zorder=3)
    ax.text(x + 0.08, cy + ROW_H / 2, 'PK', ha='left', va='center',
            fontsize=7.5, color='#bbbbbb', zorder=5)
    ax.text(x + 0.42, cy + ROW_H / 2, pk_name, ha='left', va='center',
            fontsize=8.2, color=TEXT, zorder=5)
    pk_point = (x + w, cy + ROW_H / 2)

    for attr in attrs:
        cy -= ROW_H
        ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.45, zorder=3)
        ax.text(x + 0.12, cy + ROW_H / 2, attr, ha='left', va='center',
                fontsize=8.2, color=TEXT, zorder=5)

    fk_points = {}
    for fk in fks:
        cy -= ROW_H
        ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.7, zorder=3)
        ax.text(x + 0.08, cy + ROW_H / 2, 'FK', ha='left', va='center',
                fontsize=7.5, color='#bbbbbb', zorder=5)
        ax.text(x + 0.42, cy + ROW_H / 2, fk, ha='left', va='center',
                fontsize=8.2, color=TEXT, zorder=5)
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


def _polyline(ax, pts, zorder=1):
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        ax.plot([x1, x2], [y1, y2], color=LINE, lw=1.2, zorder=zorder,
                solid_capstyle='round')


def tick_one(ax, point, direction='right'):
    x, y = point
    d = 0.12 if direction == 'right' else -0.12
    ax.plot([x, x + d], [y - 0.09, y - 0.09], color=LINE, lw=1.2, zorder=4)
    ax.plot([x, x + d], [y + 0.09, y + 0.09], color=LINE, lw=1.2, zorder=4)


def crow_many(ax, point, direction='left'):
    x, y = point
    d = -0.11 if direction == 'left' else 0.11
    for dy in (0.09, 0.0, -0.09):
        ax.plot([x, x + d], [y, y + dy], color=LINE, lw=1.15, zorder=4)


def connect_pk_fk(ax, pk_point, fk_point, lane_x):
    """Ортогональная связь 1→M: PK (справа) → полоса → FK (слева)."""
    x1, y1 = pk_point
    x2, y2 = fk_point
    direction_pk = 'right' if x2 >= x1 else 'left'
    direction_fk = 'left' if x2 >= x1 else 'right'

    _polyline(ax, [(x1, y1), (lane_x, y1), (lane_x, y2), (x2, y2)])
    tick_one(ax, pk_point, direction_pk)
    crow_many(ax, fk_point, direction_fk)


def build_er():
    fig, ax = plt.subplots(figsize=(17, 10), dpi=170)
    draw_grid(ax, (0, 17), (0, 10))

    W = 2.65

    # Колонка 1 — справочники
    auto = er_table(ax, 0.7, 6.8, W, 'Автомобили', 'КодАвто',
                    ['Наименование', 'ГосНомер', 'Марка', 'Модель'], [])
    klient = er_table(ax, 0.7, 2.2, W, 'Клиенты', 'КодКлиента',
                      ['ФИО', 'Телефон', 'Адрес'], [])

    # Колонка 2 — зависимые сущности
    ceny = er_table(ax, 6.0, 8.0, W, 'ЦеныПроката', 'КодЦены',
                    ['ЦенаЗаСутки'], ['КодАвто'])
    dogovor = er_table(ax, 6.0, 4.6, W, 'ДоговорАренды', 'Номер',
                       ['Дата', 'ДатаНачала', 'СуммаЗалога'],
                       ['КодАвто', 'КодКлиента'])
    status = er_table(ax, 6.0, 0.8, W, 'СтатусАвтопарка', 'КодСтатуса',
                      ['Статус', 'Период'], ['КодАвто'])

    # Колонка 3 — документы и отчёты
    zakrytie = er_table(ax, 11.3, 6.2, W, 'ЗакрытиеАренды', 'Номер',
                        ['ДатаВозврата', 'Пробег', 'ИтогСумма'],
                        ['НомерДоговора'])
    dohody = er_table(ax, 11.3, 2.0, W, 'ДоходыПроката', 'КодДохода',
                      ['Выручка', 'Период'], ['НомерДоговора'])

    # Полосы маршрутизации (между колонками — без пересечений)
    lane_c1_c2_a = 4.15   # Автомобили → Цены
    lane_c1_c2_b = 4.45   # Автомобили → Договор
    lane_c1_c2_c = 4.75   # Автомобили → Статус
    lane_c1_c2_d = 5.05   # Клиенты → Договор
    lane_c2_c3_a = 9.55   # Договор → Закрытие
    lane_c2_c3_b = 9.85   # Договор → Доходы

    connect_pk_fk(ax, auto['pk'], ceny['fk']['КодАвто'], lane_c1_c2_a)
    connect_pk_fk(ax, auto['pk'], dogovor['fk']['КодАвто'], lane_c1_c2_b)
    connect_pk_fk(ax, auto['pk'], status['fk']['КодАвто'], lane_c1_c2_c)
    connect_pk_fk(ax, klient['pk'], dogovor['fk']['КодКлиента'], lane_c1_c2_d)
    connect_pk_fk(ax, dogovor['pk'], zakrytie['fk']['НомерДоговора'], lane_c2_c3_a)
    connect_pk_fk(ax, dogovor['pk'], dohody['fk']['НомерДоговора'], lane_c2_c3_b)

    fig.savefig(OUT_ER, facecolor=BG, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    print('ER OK')


# ---------- USE CASE ----------

def uc_ellipse(ax, cx, cy, text, w=1.18, h=0.68, fs=7.0):
    ax.add_patch(mpatches.Ellipse(
        (cx, cy), w, h, facecolor=BOX_FILL, edgecolor=BOX_EDGE,
        linewidth=1.1, zorder=3))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs,
            color=TEXT, zorder=4, linespacing=1.05)
    return {
        'cx': cx, 'cy': cy, 'w': w, 'h': h,
        'left': cx - w / 2, 'right': cx + w / 2,
        'top': cy + h / 2, 'bottom': cy - h / 2,
    }


def uc_actor(ax, x, y, label, side='left'):
    r = 0.17
    ax.add_patch(plt.Circle((x, y), r, fill=False, edgecolor=LINE, lw=1.1, zorder=5))
    foot_y = y - 0.82
    ax.plot([x, x], [y - r, y - 0.48], color=LINE, lw=1.1, zorder=5)
    ax.plot([x - 0.2, x + 0.2], [y - 0.3, y - 0.3], color=LINE, lw=1.1, zorder=5)
    ax.plot([x, x - 0.17], [y - 0.48, foot_y], color=LINE, lw=1.1, zorder=5)
    ax.plot([x, x + 0.17], [y - 0.48, foot_y], color=LINE, lw=1.1, zorder=5)
    ax.text(x, foot_y - 0.2, label, ha='center', va='top', fontsize=8.2,
            color=TEXT, zorder=5)
    anchor = (x + 0.22, y - 0.32) if side == 'left' else (x - 0.22, y - 0.32)
    return {'anchor': anchor, 'side': side, 'x': x, 'y': y}


def link_actor_uc(ax, actor, uc, lane=0, dashed=False, side='left'):
    """Прямая ортогональная связь актор → овал (каждая линия отдельно)."""
    ax0, ay0 = actor['anchor']
    ls = '--' if dashed else '-'
    lw = 1.45

    if side == 'left':
        mid_x = ax0 + 0.28 + lane * 0.24
        tx, ty = uc['left'], uc['cy']
    else:
        mid_x = ax0 - 0.28 - lane * 0.24
        tx, ty = uc['right'], uc['cy']

    pts = [(ax0, ay0), (mid_x, ay0), (mid_x, ty), (tx, ty)]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        ax.plot([x1, x2], [y1, y2], color=LINE, lw=lw, ls=ls, zorder=1,
                solid_capstyle='round')


def link_actor_group(ax, actor, ucs, side='left', dashed=False):
    for i, uc in enumerate(ucs):
        link_actor_uc(ax, actor, uc, lane=i, dashed=dashed, side=side)


def build_use_case():
    # Вертикальный формат — не «плоский», связи хорошо видны
    fig, ax = plt.subplots(figsize=(8.5, 10.5), dpi=180)
    draw_grid(ax, (0, 8.5), (0, 10.5))

    bx, by, bw, bh = 1.85, 1.35, 4.85, 7.55
    ax.add_patch(FancyBboxPatch(
        (bx, by), bw, bh, boxstyle='square,pad=0.02',
        facecolor='none', edgecolor=BOX_EDGE, linewidth=1.8, zorder=2))
    ax.text(bx + bw / 2, by + bh + 0.3, 'ИС учёта аренды автомобилей',
            ha='center', va='bottom', fontsize=10.5, color=TEXT, fontweight='bold')

    xs = [2.75, 4.35, 5.95]
    ys = [7.55, 5.35, 3.15]
    labels = [
        ['Управление\nпользователями', 'Управление\nправами', 'Ведение\nсправочников'],
        ['Регистрация\nклиента', 'Оформление\nдоговора\nаренды', 'Закрытие\nаренды'],
        ['Учёт пробега\nи доплат', 'Отчёт\n«Автопарк»', 'Отчёт\n«Доходы»'],
    ]
    ucs = []
    for row, y in enumerate(ys):
        row_uc = []
        for col, x in enumerate(xs):
            row_uc.append(uc_ellipse(ax, x, y, labels[row][col], w=1.15, h=0.78, fs=7.1))
        ucs.append(row_uc)

    # Акторы по высоте рядом со «своими» вариантами
    admin = uc_actor(ax, 0.45, 7.55, 'Администратор', 'left')
    mgr = uc_actor(ax, 0.45, 4.85, 'Менеджер', 'left')
    director = uc_actor(ax, 8.05, 3.15, 'Директор', 'right')
    client = uc_actor(ax, 8.05, 5.35, 'Клиент', 'right')

    link_actor_group(ax, admin, ucs[0], 'left')
    link_actor_group(ax, mgr, ucs[1] + [ucs[2][0]], 'left')
    link_actor_group(ax, director, ucs[2][1:], 'right')
    link_actor_group(ax, client, [ucs[1][1], ucs[1][2]], 'right', dashed=True)

    fig.savefig(OUT_UC, facecolor=BG, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    print('UC OK')


if __name__ == '__main__':
    build_er()
    build_use_case()
