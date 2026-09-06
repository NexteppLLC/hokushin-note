"""Run with python -m unittest discover -s tests -p 'test_exercise_context.py'."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
from export_json import split_items, split_item_block, parse
from export_app import build_subject, linked_mock_questions
import editions as ED


class ExerciseContextTests(unittest.TestCase):
    def test_shared_table_figure_and_prose_survive_split(self):
        prefix = '資料A：観察の条件\n\n| 実験 | 結果 |\n|:--|:--|\n| A | 変化した |\n\n[[svg:circuit_sp]]'
        block = split_item_block(prefix + '\n\n(1) 何を比べるか。\n(2) 理由を答えよ。')
        self.assertEqual(block['context_md'], prefix)
        self.assertEqual([i['no'] for i in block['items']], [1, 2])
        self.assertNotIn('資料A', block['items'][0]['text'])
        self.assertEqual(block['items'], split_items(prefix + '\n\n(1) 何を比べるか。\n(2) 理由を答えよ。'))

    def test_existing_inline_numbers_keep_their_values(self):
        items = split_items('8. 前半　9. 中盤　10. 後半')
        self.assertEqual([i['no'] for i in items], [8, 9, 10])
        self.assertIsNone(split_item_block('1. A\n3. B'))

    def test_h5_circuit_and_history_context_present(self):
        ed = ED.by_id('h5')
        science = build_subject('science', 'S', '理科', '理', ed)
        social = build_subject('social', 'H', '社会', '社', ed)
        circuit = next(u for u in science['units'] if u['code'] == 'R13')['content'][2]
        self.assertIn('<svg', circuit['context'])
        self.assertEqual([i['n'] for i in circuit['items']], list(range(1, 8)))
        self.assertTrue(all('<svg' not in i['q'] for i in circuit['items']))
        history = next(u for u in social['units'] if u['code'] == 'R2')
        context = '\n'.join(c.get('context', '') for c in history['content'])
        self.assertIn('望月', context)
        self.assertIn('資料', context)

    def test_mock_questions_link_only_to_their_own_answer_set(self):
        ed = ED.by_id('h5')
        for sid, key, name, short, count in [('science', 'S', '理科', '理', 5), ('social', 'H', '社会', '社', 6)]:
            sub = build_subject(sid, key, name, short, ed)
            for code in ['M1', 'M2']:
                mock = next(u for u in sub['units'] if u['code'] == code)
                questions = [c for c in mock['content'] if c['t'] == 'ex']
                self.assertEqual(len(questions), count)
                self.assertTrue(all(c['a'] and c['contextTitle'].startswith('大問') for c in questions))
                self.assertTrue(all(c['t'] != 'q' for c in mock['content']))
                # Original answer units remain present; note/ink indices cannot shift.
                answers = [u for u in sub['units'] if u['code'] == code and '解答' in u['title']]
                self.assertEqual(len(answers), 1)

    def test_ambiguous_answer_set_is_not_guessed(self):
        sec = {'file': 'mock.md', 'path': ['章', 'M1　模試', '大問1'], 'heading': '大問1', 'blocks': [{'type': 'q', 'title': '問題', 'md': '1. A\n2. B'}]}
        ans = {'file': 'mock.md', 'path': ['章', 'M1　解答'], 'heading': 'M1　解答', 'blocks': [{'type': 'a', 'title': '大問1', 'md': '1. A\n2. B'}] * 2}
        self.assertEqual(linked_mock_questions({'sections': [sec, ans]}), {})


if __name__ == '__main__':
    unittest.main()
