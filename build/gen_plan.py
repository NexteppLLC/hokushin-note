# -*- coding: utf-8 -*-
"""Generate master plan markdown, per-subject plan tables, and data/plan.json."""
import os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
import editions as ED
EDITION, _args = ED.resolve(sys.argv[1:])
_pd = ED.import_module(EDITION, 'plan_data')
globals().update({k: v for k, v in vars(_pd).items() if not k.startswith('__')})

# Earlier editions can retain their unit-based plan without overrides.
if not hasattr(_pd, 'task_min'):
    def task_min(day, subj, code):
        return unit_min(subj, code)
if not hasattr(_pd, 'task_title'):
    def task_title(day, subj, code):
        return unit_title(subj, code)
if not hasattr(_pd, 'task_scope'):
    def task_scope(day, subj, code):
        return 'unit'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
days = day_list()

SUBJ_FILE = {'E': 'english', 'M': 'math', 'J': 'japanese', 'S': 'science', 'H': 'social'}


def fmt_date(d):
    return '%d/%d（%s）' % (d['date'].month, d['date'].day, d['wd'])


def subject_plan_md(subj):
    """Table for a subject's own PDF: Day, date, tasks, minutes."""
    lines = []
    lines.append('| Day | 日付 | 区分 | 今日やること（教材の番号） | 目安 | 済 |')
    lines.append('|:--:|:--|:--:|:--|--:|:--:|')
    for d in days:
        codes = d['tasks'][subj]
        items = '／'.join('**%s** %s' % (c, task_title(d['day'], subj, c)) for c in codes)
        m = sum(task_min(d['day'], subj, c) for c in codes)
        kind = '休日' if d['is_h'] else '平日'
        if d['holiday']:
            kind = '祝日'
        lines.append('| %d | %s | %s | %s | %d分 | ☐ |' % (d['day'], fmt_date(d), kind, items, m))
    return '\n'.join(lines)


def master_md():
    out = []
    out.append('# 34日間の日別タスク表')
    out.append('')
    out.append('各日の「番号」は科目別教材の番号です。時間は当日の指定範囲の目安です。「必要知識10分」は該当箇所だけを確認する枠で、単元全体の学習完了を意味しません。理科・社会は解答を見ずに図資料を解き、直しと24時間以上あけた再テストを分けます。余った時間を無理に埋める必要はありません。')
    out.append('')
    week = 0
    for d in days:
        if d['date'].weekday() == 0 or d['day'] == 1:
            week += 1
            out.append('## 第%d週' % week)
            out.append('')
        budget = HOLIDAY_MIN if d['is_h'] else WEEKDAY_MIN
        kind = '休日（配分は下表）' if d['is_h'] else '平日（配分は下表）'
        if d['holiday']:
            kind = '祝日（%s）' % d['holiday']
        total = sum(sum(task_min(d['day'], s, c) for c in d['tasks'][s]) for s in SUBJ_ORDER)
        out.append('<div class="dayhead">Day %d　%s　%s　<span class="gray">合計の目安 %d分</span></div>' % (d['day'], fmt_date(d), kind, total))
        out.append('')
        if d['day'] in DAY_NOTES:
            out.append('<p class="small">※ %s</p>' % DAY_NOTES[d['day']])
            out.append('')
        out.append('| 科目 | やること（番号は科目別PDFの番号） | 目安 | 済 |')
        out.append('|:--|:--|--:|:--:|')
        for s in SUBJ_ORDER:
            codes = d['tasks'][s]
            items = '<br>'.join('**%s** %s' % (c, task_title(d['day'], s, c)) for c in codes)
            m = sum(task_min(d['day'], s, c) for c in codes)
            out.append('| %s | %s | %d分 | ☐ |' % (SUBJ_NAME[s], items, m))
        out.append('')
    return '\n'.join(out)


def calendar_md():
    out = []
    out.append('| 週 | 月 | 火 | 水 | 木 | 金 | 土 | 日 |')
    out.append('|:--:|:--|:--|:--|:--|:--|:--|:--|')
    row = []
    week = 1
    for d in days:
        if d['date'].weekday() == 0:
            row = []
        label = 'Day%d<br>%d/%d' % (d['day'], d['date'].month, d['date'].day)
        if d['holiday']:
            label += '<br><span class="red">%s</span>' % d['holiday']
        if d['day'] == 14:
            label += '<br><span class="red">申込締切</span>'
        if d['day'] in (17, 20):
            label += '<br>模擬①'
        if d['day'] == 27:
            label += '<br>模擬②'
        if d['day'] == 34:
            label += '<br>前日'
        row.append(label)
        if d['date'].weekday() == 6 or d['day'] == 34:
            if d['day'] == 34:
                row.append('<span class="red">10/11<br>北辰テスト<br>第5回</span>')
            out.append('| %d | %s |' % (week, ' | '.join(row)))
            week += 1
    return '\n'.join(out)


def write_plan_json():
    data = {'start': str(START), 'test_day': str(TEST_DAY), 'weekday_minutes': WEEKDAY_MIN, 'holiday_minutes': HOLIDAY_MIN,
            'subjects': {s: SUBJ_NAME[s] for s in SUBJ_ORDER}, 'units': {}, 'days': []}
    for s in SUBJ_ORDER:
        data['units'][s] = {}
        for code, (title, mins) in UNITS[s].items():
            data['units'][s][code] = {'title': title, 'minutes': mins}
        if s == 'J':
            for i in range(1, 31):
                data['units'][s]['K%d' % i] = {'title': '漢字セット%d' % i, 'minutes': 10}
            data['units'][s].pop('K', None)
    for d in days:
        data['days'].append({'day': d['day'], 'date': str(d['date']), 'weekday': d['wd'], 'holiday': d['holiday'], 'is_holiday': d['is_h'],
                             'note': DAY_NOTES.get(d['day']), 'tasks': {s: [{'code': c, 'title': task_title(d['day'], s, c), 'minutes': task_min(d['day'], s, c), 'scope': task_scope(d['day'], s, c)} for c in d['tasks'][s]] for s in SUBJ_ORDER}})
    json.dump(data, open(ED.data_dir(EDITION, 'plan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    os.makedirs(ED.src_dir(EDITION, 'plan'), exist_ok=True)
    open(ED.src_dir(EDITION, 'plan', '90_days.md'), 'w', encoding='utf-8').write(master_md())
    open(ED.src_dir(EDITION, 'plan', 'calendar.inc.md'), 'w', encoding='utf-8').write(calendar_md())
    for s in SUBJ_ORDER:
        sd = ED.src_dir(EDITION, SUBJ_FILE[s])
        os.makedirs(sd, exist_ok=True)
        open(os.path.join(sd, 'plan_table.inc.md'), 'w', encoding='utf-8').write(subject_plan_md(s))
    write_plan_json()
    print('ok')
