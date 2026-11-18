import json,unittest,tempfile,shutil
from pathlib import Path
import pyarrow.parquet as pq
from materials.physical import load_inventory
ROOT=Path(__file__).resolve().parents[1]

class InputMaterials(unittest.TestCase):
    def test_json_parquet_values_and_inventory(self):
        self.assertTrue(load_inventory(ROOT/'inputs'))
        seed=json.loads((ROOT/'inputs/seed.json').read_text(encoding='utf-8'))
        for name,rows in seed.items():
            self.assertEqual(pq.read_table(ROOT/'inputs'/(name+'.parquet')).to_pylist(),rows,name)

    def test_modified_raw_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'inputs';shutil.copytree(ROOT/'inputs',target)
            inv=json.loads((target/'inventory.json').read_text(encoding='utf-8'))
            p=target/inv['files'][0]['path'];p.write_bytes(p.read_bytes()+b'x')
            with self.assertRaisesRegex(ValueError,'摘要'):load_inventory(target)

    def test_domain_material_references_and_edge_states(self):
        seed=json.loads((ROOT/'inputs/seed.json').read_text(encoding='utf-8'))
        actions=json.loads((ROOT/'inputs/actions.json').read_text(encoding='utf-8'))
        assignments=seed['assignments'];enrollment=seed['enrollment']
        self.assertEqual(len({(x['cluster'],x['block']) for x in assignments}),len(assignments))
        for block in {x['block'] for x in assignments}:
            for stratum in {x['design_stratum'] for x in assignments}:
                part=[x for x in assignments if x['block']==block and x['design_stratum']==stratum]
                self.assertEqual(sum(x['arm']=='offer' for x in part),2)
        orders={x['order'] for x in seed['orders']}
        self.assertTrue(all(x['order'] in orders for x in seed['refunds']+seed['subsidies']))
        self.assertIn(actions[0]['row']['order'],orders)
        self.assertTrue(any(x['cross_cluster'] is None for x in seed['exposures']))
