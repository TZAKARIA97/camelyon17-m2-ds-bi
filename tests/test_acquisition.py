"""Tester les lectures HTTP bornées sans utiliser le réseau ni les données médicales."""
import io
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from src.data.acquire_wilds import RangeReader, safe_target
from src.data.wilds_manifest import convert
from src.data.annotations import read_xml, local_mask
import pandas as pd


class Response(io.BytesIO):
    def __init__(self, payload, status, content_range):
        super().__init__(payload)
        self.status = status
        self.headers = {'Content-Range': content_range}


class RangeTests(unittest.TestCase):
    def test_official_tumor_xml_alias_produces_a_positive_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'example.xml'
            path.write_text('<ASAP_Annotations><Annotations><Annotation PartOfGroup="Tumor">'
                            '<Coordinates><Coordinate Order="0" X="0" Y="0"/>'
                            '<Coordinate Order="1" X="8" Y="0"/>'
                            '<Coordinate Order="2" X="0" Y="8"/></Coordinates>'
                            '</Annotation></Annotations></ASAP_Annotations>')
            polygons = read_xml(path)
            self.assertEqual(polygons[0].group, 'metastases')
            self.assertGreater(float(local_mask(polygons, 0, 0, 16).mean()), 0)

    def test_id_validation_is_explicitly_excluded_without_reassigning_train(self):
        with tempfile.TemporaryDirectory() as tmp:
            pd.DataFrame({'patient':['001','001','002','003'], 'node':[0]*4,
                          'x_coord':[1,2,3,4], 'y_coord':[1]*4, 'center':[0,0,1,2],
                          'tumor':[0,1,0,1], 'split':[0,1,0,0]}).to_csv(Path(tmp)/'metadata.csv',index=False)
            with self.assertRaisesRegex(ValueError, 'Fuite'):
                convert(tmp)
            result = convert(tmp, 'exclude-id-val')
            self.assertEqual(result.split.tolist(), ['train','val','test'])
            self.assertEqual(result.x.tolist(), [1,3,4])
            self.assertTrue((result.original_split == result.split).all())

    def test_zip_read_and_crc_through_partial_http(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('camelyon17_v1.0/metadata.csv', 'patient,node\n001,0\n')
        payload = buffer.getvalue()
        requests = []
        def response(request, **kwargs):
            start, end = map(int, re.fullmatch(r'bytes=(\d+)-(\d+)', request.get_header('Range')).groups())
            requests.append((start, end))
            return Response(payload[start:end+1], 206, f'bytes {start}-{end}/{len(payload)}')
        with patch('src.data.acquire_wilds.urlopen', side_effect=response):
            reader = RangeReader('https://example.invalid/archive.zip', len(payload))
            with zipfile.ZipFile(reader) as archive:
                self.assertEqual(archive.read('camelyon17_v1.0/metadata.csv'), b'patient,node\n001,0\n')
        self.assertTrue(requests)

    def test_full_download_response_is_refused(self):
        response = Response(b'', 200, '')
        with patch('src.data.acquire_wilds.urlopen', return_value=response), self.assertRaisesRegex(ValueError, 'plage'):
            RangeReader('https://example.invalid', 10_000_000).read(1)

    def test_truncated_range_and_budget_are_rejected(self):
        with patch('src.data.acquire_wilds.urlopen', return_value=Response(b'a', 206, 'bytes 0-99/100')):
            with self.assertRaisesRegex(ValueError, 'tronquée'):
                RangeReader('https://example.invalid', 100).read(5)
        with patch('src.data.acquire_wilds.urlopen') as network:
            with self.assertRaisesRegex(ValueError, 'Budget'):
                RangeReader('https://example.invalid', 100_000, budget=10).read(1)
            network.assert_not_called()

    def test_paths_cannot_escape_data_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(safe_target(root, 'camelyon17_v1.0/metadata.csv'), root/'camelyon17_v1.0/metadata.csv')
            for name in ('../secret', '/tmp/secret', 'camelyon17_v1.0/../../secret', 'another_dataset/image.png'):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    safe_target(root, name)


if __name__ == '__main__':
    unittest.main()
