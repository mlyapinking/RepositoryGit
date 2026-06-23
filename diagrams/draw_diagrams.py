#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ER и Use Case диаграммы в стиле курсовой (тёмная сетка, компактный use case)."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

OUT_ER = '/workspace/diagrams/05_er_diagram.png'
OUT_UC = '/workspace/diagrams/01_use_case.png'

# --- стиль «как в примере» ---
BG = '#1e1e1e'
GRID = '#3a3a3a'
BOX_FILL = '#2b2b2b'
BOX_EDGE = '#ffffff'
TEXT = '#ffffff'
LINE = '#ffffff'


def draw_grid(ax, xlim, ylim, step=0.5):
    ax.set_facecolor(BG)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect('equal')
    ax.axis('off')
    for x in np.arange(xlim[0], xlim[1] + step, step):
        ax.axvline(x, color=GRID, linewidth=0.4, zorder=0)
    for y in np.arange(ylim[0], ylim[1] + step, step):
        ax.axhline(y, color=GRID, linewidth=0.4, zorder=0)


def er_table(ax, x, y, w, h, title, pk, attrs, fks=None):
  """Прямоугольник таблицы с секциями PK / поля / FK."""
  fks = fks or []
  total_h = h
  ax.add_patch(FancyBboxPatch((x, y), w, total_h, boxstyle='square,pad=0.01',
                               facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.5, zorder=2))
  # заголовок
  header_h = 0.55
  ax.plot([x, x + w], [y + total_h - header_h, y + total_h - header_h], color=BOX_EDGE, lw=1, zorder=3)
  ax.text(x + w/2, y + total_h - header_h/2, title, ha='center', va='center',
          fontsize=11, color=TEXT, fontweight='bold', zorder=4)
  cy = y + total_h - header_h
  row_h = 0.38
  # PK
  if pk:
    cy -= row_h
    ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.8, zorder=3)
    ax.text(x + 0.12, cy + row_h/2, 'PK', ha='left', va='center', fontsize=8, color='#cccccc', zorder=4)
    ax.text(x + 0.55, cy + row_h/2, pk, ha='left', va='center', fontsize=9, color=TEXT, zorder=4)
  # attrs
  for a in attrs:
    cy -= row_h
    ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.6, zorder=3)
    ax.text(x + 0.18, cy + row_h/2, a, ha='left', va='center', fontsize=9, color=TEXT, zorder=4)
  # FK
  for fk in fks:
    cy -= row_h
    ax.plot([x, x + w], [cy, cy], color=BOX_EDGE, lw=0.8, zorder=3)
    ax.text(x + 0.12, cy + row_h/2, 'FK', ha='left', va='center', fontsize=8, color='#cccccc', zorder=4)
    ax.text(x + 0.55, cy + row_h/2, fk, ha='left', va='center', fontsize=9, color=TEXT, zorder=4)
  return {
    'cx': x + w/2, 'top': y + total_h, 'bottom': y,
    'left': x, 'right': x + w,
    'mid_left': (x, y + total_h/2), 'mid_right': (x + w, y + total_h/2),
    'mid_top': (x + w/2, y + total_h), 'mid_bottom': (x + w/2, y)
  }


def crow_foot(ax, p1, p2, side='right'):
  """Линия связи 1 ко многим (упрощённо)."""
  ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=LINE, lw=1.2, zorder=1)
  # перпендикулярная черта на стороне «один»
  dx, dy = p2[0]-p1[0], p2[1]-p1[1]
  L = (dx**2+dy**2)**0.5 or 1
  ux, uy = dx/L, dy/L
  px, py = -uy, ux
  if side == 'one_at_p2':
    ox, oy = p2[0] - ux*0.15, p2[1] - uy*0.15
    ax.plot([ox+px*0.12, ox-px*0.12], [oy+py*0.12, oy-py*0.12], color=LINE, lw=1.2, zorder=1)
    # вилка «много» у p1
    ax.plot([p1[0]+px*0.1, p1[0]-px*0.08+ux*0.05, p1[0]-px*0.08-ux*0.05],
            [p1[1]+py*0.1, p1[1]-py*0.08+uy*0.05, p1[1]-py*0.08-uy*0.05], color=LINE, lw=1.2, zorder=1)


def build_er():
  fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
  draw_grid(ax, (0, 14), (0, 10))

  # Позиции как в образце склада цветов, сущности — аренда авто
  t_auto = er_table(ax, 0.8, 6.8, 2.6, 2.5, 'Автомобили', 'КодАвтомобиля',
                    ['Наименование', 'ГосНомер', 'Марка', 'Модель'])
  t_tip = er_table(ax, 0.8, 3.8, 2.6, 1.5, 'ТипКлиента', 'КодТипа', ['Значения'])
  t_kl = er_table(ax, 0.8, 0.8, 2.6, 2.2, 'Клиенты', 'КодКлиента',
                  ['наименование', 'Адрес'], ['ТипКлиента'])
  t_sotr = er_table(ax, 5.5, 0.5, 2.8, 2.6, 'Сотрудники', 'КодСотрудника',
                    ['Наименование', 'Дата', 'НомерТелефона', 'Должность'])
  t_punkt = er_table(ax, 9.2, 0.5, 2.6, 2.2, 'ПунктВыдачи', 'КодПункта',
                     ['Наименование'], ['Сотрудники', 'Сотрудник', 'Автомобиль'])
  t_dog = er_table(ax, 9.0, 4.5, 3.0, 2.6, 'ДоговорАренды', 'КодДоговора',
                   ['Дата', 'КоличествоСуток', 'Номер'],
                   ['Автомобиль', 'ПунктВыдачи', 'Клиент'])
  t_stat = er_table(ax, 9.0, 7.8, 3.0, 1.9, 'СтатусАвтопарка', 'КодСтатуса',
                    ['статус', 'период'], ['автомобиль', 'Договоры'])

  # связи (как в образце)
  crow_foot(ax, t_auto['mid_right'], (t_dog['left'], t_dog['mid_left'][1]))
  crow_foot(ax, (t_auto['mid_right'][0], t_auto['mid_right'][1]-0.5), (t_punkt['left'], t_punkt['mid_left'][1]+0.3))
  crow_foot(ax, (t_auto['mid_top'][0]+0.3, t_auto['top']), (t_stat['mid_bottom'][0]-0.5, t_stat['bottom']))

  crow_foot(ax, t_tip['mid_right'], t_kl['mid_left'])
  crow_foot(ax, t_kl['mid_right'], (t_dog['left'], t_dog['mid_left'][1]-0.5))

  crow_foot(ax, t_sotr['mid_right'], (t_punkt['left'], t_punkt['mid_left'][1]-0.2))
  crow_foot(ax, (t_sotr['mid_right'][0], t_sotr['mid_right'][1]+0.4), (t_punkt['left'], t_punkt['mid_left'][1]+0.5))

  crow_foot(ax, t_punkt['mid_top'], (t_dog['mid_bottom'][0]-0.8, t_dog['bottom']))
  crow_foot(ax, t_dog['mid_top'], t_stat['mid_bottom'])

  fig.savefig(OUT_ER, facecolor=BG, bbox_inches='tight', pad_inches=0.15)
  plt.close(fig)
  print('ER:', OUT_ER)


def uc_ellipse(ax, cx, cy, w, h, text, fs=8):
  e = mpatches.Ellipse((cx, cy), w, h, facecolor=BOX_FILL, edgecolor=BOX_EDGE, linewidth=1.2, zorder=3)
  ax.add_patch(e)
  ax.text(cx, cy, text, ha='center', va='center', fontsize=fs, color=TEXT, wrap=True, zorder=4)


def uc_actor(ax, x, y, label, stick_down=True):
  # голова
  ax.add_patch(plt.Circle((x, y), 0.22, fill=False, edgecolor=LINE, lw=1.2, zorder=4))
  # тело
  if stick_down:
    ax.plot([x, x], [y-0.22, y-0.75], color=LINE, lw=1.2, zorder=4)
    ax.plot([x-0.28, x+0.28], [y-0.45, y-0.45], color=LINE, lw=1.2, zorder=4)
    ax.plot([x, x-0.22], [y-0.75, y-1.0], color=LINE, lw=1.2, zorder=4)
    ax.plot([x, x+0.22], [y-0.75, y-1.0], color=LINE, lw=1.2, zorder=4)
    ax.text(x, y-1.25, label, ha='center', va='top', fontsize=9, color=TEXT, zorder=4)
    return (x, y-1.0)
  else:
    ax.plot([x, x], [y+0.22, y+0.75], color=LINE, lw=1.2, zorder=4)
    ax.plot([x-0.28, x+0.28], [y+0.45, y+0.45], color=LINE, lw=1.2, zorder=4)
    ax.plot([x, x-0.22], [y+0.75, y+1.0], color=LINE, lw=1.2, zorder=4)
    ax.plot([x, x+0.22], [y+0.75, y+1.0], color=LINE, lw=1.2, zorder=4)
    ax.text(x, y+1.28, label, ha='center', va='bottom', fontsize=9, color=TEXT, zorder=4)
    return (x, y+1.0)


def build_use_case():
  fig, ax = plt.subplots(figsize=(8, 8), dpi=180)
  draw_grid(ax, (0, 8), (0, 8))

  # граница системы — КВАДРАТ
  bx, by, bw, bh = 1.6, 1.4, 4.8, 5.2
  ax.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle='square,pad=0.02',
                               facecolor='none', edgecolor=BOX_EDGE, linewidth=2, zorder=2))
  ax.text(bx + bw/2, by + bh + 0.25, 'ИС учёта аренды автомобилей', ha='center', va='bottom',
          fontsize=10, color=TEXT, fontweight='bold')

  # use cases — компактная сетка 3x3 внутри квадрата
  cases = [
    (2.4, 5.8, 'Управление\nпользователями'),
    (4.0, 5.8, 'Управление\nправами'),
    (5.6, 5.8, 'Ведение\nсправочников'),
    (2.4, 4.2, 'Регистрация\nклиента'),
    (4.0, 4.2, 'Оформление\nдоговора аренды'),
    (5.6, 4.2, 'Закрытие\nаренды'),
    (2.4, 2.6, 'Учёт пробега\nи доп. расходов'),
    (4.0, 2.6, 'Отчёт\n«Автопарк»'),
    (5.6, 2.6, 'Отчёт «Доходы\nот проката»'),
  ]
  centers = []
  for cx, cy, txt in cases:
    uc_ellipse(ax, cx, cy, 1.35, 0.85, txt, fs=7.5)
    centers.append((cx, cy, txt))

  # акторы по углам квадрата
  a_admin = uc_actor(ax, 0.7, 6.5, 'Администратор', stick_down=True)
  a_mgr = uc_actor(ax, 0.7, 3.2, 'Менеджер', stick_down=True)
  a_dir = uc_actor(ax, 7.3, 5.0, 'Директор', stick_down=False)
  a_cli = uc_actor(ax, 7.3, 2.0, 'Клиент', stick_down=False)

  def link(actor, cx, cy):
    ax.plot([actor[0], cx], [actor[1], cy], color=LINE, lw=0.9, linestyle='-', zorder=1)

  # связи админ
  for cx, cy, t in centers[:3]:
    link(a_admin, cx, cy)
  # менеджер
  for cx, cy, t in centers[3:7]:
    link(a_mgr, cx, cy)
  # директор
  for cx, cy, t in centers[7:]:
    link(a_dir, cx, cy)
  # клиент — пунктир к договору
  ax.plot([a_cli[0], 4.0], [a_cli[1], 4.2], color=LINE, lw=0.9, linestyle='--', zorder=1)

  fig.savefig(OUT_UC, facecolor=BG, bbox_inches='tight', pad_inches=0.1)
  plt.close(fig)
  print('UC:', OUT_UC)


if __name__ == '__main__':
  build_er()
  build_use_case()
