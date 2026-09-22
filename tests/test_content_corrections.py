"""Regression checks for grouped Japanese answers and the parallel-line figure."""
import math
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build'))
from export_json import pair_numbered_groups
from export_app import build_subject
import editions as ED


class ContentCorrectionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.japanese = build_subject('japanese', 'J', '国語', '国', ED.by_id('h5'))

    def test_all_five_mock_answer_sets_and_existing_block_positions(self):
        keys = {
            'M1': ['ア', 'イ', 'イ', '昇降口'],
            'M2': ['イ', 'イ', 'ア', '五枚'],
            'M3': ['ウ', 'イ', 'イ', '呼びかけ'],
            'M4': ['イ', 'ア', 'イ', '用意しておくとよい物のリスト'],
            'M5': ['イ', 'イ', 'ア', '一緒に歌えて楽しいと思うから。'],
        }
        for code, expected in keys.items():
            with self.subTest(code=code):
                u = next(u for u in self.japanese['units'] if u['code'] == code)
                blocks = u['content']
                # Four earlier question blocks and the original passage/data slots stay put.
                self.assertEqual([b['t'] for b in blocks[:5]], ['ex'] * 4 + ['dialog'])
                fifth_index = 5 if code == 'M2' else 6
                fifth = blocks[fifth_index]
                self.assertEqual(fifth['title'], '問5の問い')
                self.assertEqual([i['n'] for i in fifth['items']], [1, 2, 3, 4])
                self.assertEqual(len(blocks[0]['items']), 3)
                self.assertEqual(len(blocks[1]['items']), 2)
                for item, answer in zip(fifth['items'], expected):
                    text = re.sub('<[^>]+>', '', item['a']).strip()
                    self.assertTrue(text.startswith(answer), (text, answer))
                    self.assertNotIn('記録', text)
                self.assertIn(blocks[4]['html'], fifth['externalContext'])

    def test_m2_reading_writing_and_grammar_answers(self):
        blocks = next(u for u in self.japanese['units'] if u['code'] == 'M2')['content']
        for item, expected in zip(blocks[0]['items'], ['せいじゃく', 'むじゅん', 'こめて']):
            self.assertEqual(re.sub('<[^>]+>', '', item['a']).strip(), expected)
        self.assertIn('ユタ', blocks[1]['items'][1]['q'])
        self.assertIn('豊', blocks[1]['items'][1]['a'])
        self.assertIn('ア（形容詞', blocks[2]['a'])
        self.assertIn('イ（火を消す', blocks[3]['a'])

    def test_mismatched_or_duplicate_group_numbers_fail_build(self):
        for answer in ['問1　A\n問3　C', '問1　A\n問1　B']:
            with self.assertRaises(ValueError):
                pair_numbered_groups([
                    {'type': 'q', 'title': '問1　問題', 'md': 'A'},
                    {'type': 'q', 'title': '問2　問題', 'md': 'B'},
                    {'type': 'a', 'title': '解答', 'md': answer},
                ])

    def test_svg_angles_match_the_stated_geometry(self):
        root = ET.parse(ROOT / 'src/h5/math/figs/d2_8_angles.svg').getroot()
        ns = {'s': 'http://www.w3.org/2000/svg'}
        lines = root.find('s:g', ns).findall('s:line', ns)
        points = lambda line: [(float(line.get('x' + str(i))), float(line.get('y' + str(i)))) for i in (1, 2)]
        top, bottom, upper, lower = [points(line) for line in lines[:4]]
        self.assertEqual(top[0][1], top[1][1])
        self.assertEqual(bottom[0][1], bottom[1][1])
        p1, vertex = upper
        self.assertEqual(vertex, lower[0])
        p2 = lower[1]
        self.assertLess(p1[0], vertex[0])
        self.assertLess(p2[0], vertex[0])
        angle = lambda p, v: math.degrees(math.atan2(abs(p[1] - v[1]), abs(p[0] - v[0])))
        self.assertAlmostEqual(angle(p1, vertex), 55, delta=.1)
        self.assertAlmostEqual(angle(p2, vertex), 30, delta=.1)
        self.assertAlmostEqual(angle(p1, vertex) + angle(p2, vertex), 85, delta=.15)


if __name__ == '__main__':
    unittest.main()
