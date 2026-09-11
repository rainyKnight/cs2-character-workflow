import copy
import hashlib
import json
import pathlib
import struct
import subprocess
import sys
import unittest
import uuid

ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skill/scripts'
sys.path.insert(0,str(SCRIPTS))
import workflow
import create_project

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'test-runs'/uuid.uuid4().hex
        self.root.mkdir(parents=True)
        self.writer=self.root/'write.py'
        self.writer.write_text('import pathlib,sys\np=pathlib.Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True);p.write_text("artifact");print("OK")\n')

    def invoke(self,*args,code=0):
        p=subprocess.run([sys.executable,'-X','utf8',str(SCRIPTS/'workflow.py'),*map(str,args)],capture_output=True,text=True,encoding='utf8')
        self.assertEqual(p.returncode,code,(p.stdout,p.stderr))
        return p

    def config(self):
        return {'schema':1,'mode':'auto','checkpoints':[], 'stages':[
            {'id':s,'kind':'command','argv':['{python}',str(self.writer),'{run}/'+s+'.txt'],
             'outputs':[s+'.txt'],'success_marker':'OK'} for s in ['a','b']]}

    def start(self,c,code=0):
        p=self.root/'config.json';workflow.save(p,c);run=self.root/'run'
        self.invoke('start',p,'--run',run,code=code);return run

    def test_auto_and_finished_resume(self):
        run=self.start(self.config());self.invoke('resume',run)
        self.assertEqual(workflow.read(run/'state.json')['completed'],['a','b'])

    def test_gate_requires_exact_explicit_acceptance(self):
        c=self.config();c.update(mode='checkpoints',checkpoints=['a']);run=self.start(c,2)
        self.invoke('resume',run,code=2);self.assertFalse((run/'b.txt').exists())
        self.invoke('accept',run,'b','--note','wrong gate',code=1)
        self.invoke('accept',run,'a','--note','Fixture operator decision, no game validation')
        self.assertTrue((run/'b.txt').exists())

    def test_authoring_record_cannot_bypass_review(self):
        c=self.config();c.update(mode='checkpoints',checkpoints=['a']);c['stages'][0]={'id':'a','kind':'agent','outputs':['a.txt']}
        run=self.start(c,2);(run/'a.txt').write_text('authored fixture')
        ev=self.root/'evidence.json';workflow.save(ev,{'status':'passed','summary':'Created test artifact','checks':['fixture exists']})
        self.invoke('record',run,'a','--evidence',ev,code=2)
        self.assertEqual(workflow.read(run/'state.json')['status'],'awaiting_review')
        self.assertFalse((run/'b.txt').exists())

    def test_edited_output_is_detected(self):
        run=self.start(self.config());(run/'a.txt').write_text('edited');self.invoke('resume',run,code=1)

    def test_corrupt_snapshot_is_detected(self):
        run=self.start(self.config());(run/'checkpoints/a/a.txt').write_text('edited');self.invoke('resume',run,code=1)

    def test_changed_config_is_detected(self):
        run=self.start(self.config());c=workflow.read(run/'config.json');c['mode']='checkpoints';workflow.save(run/'config.json',c)
        self.invoke('resume',run,code=1)

    def test_missing_success_marker_stops_downstream(self):
        c=self.config();c['stages'][0]['success_marker']='ABSENT';run=self.start(c,1)
        self.assertFalse((run/'b.txt').exists())

    def test_missing_output_stops_downstream(self):
        c=self.config();c['stages'][0]['outputs']=['missing'];run=self.start(c,1)
        self.assertFalse((run/'b.txt').exists())

    def test_path_escape_rejected(self):
        c=self.config();c['stages'][0]['outputs']=['../escape']
        with self.assertRaises(ValueError):workflow.validate(c)

    def test_two_distinct_user_sources_share_only_hand_asset(self):
        projects=[]
        for label in ['character_one','unrelated_character']:
            source=self.root/(label+'.fbx');source.write_bytes(b'input fixture; not a real model')
            cfg=create_project.create(label,source,self.root/label,['physics'])
            projects.append(workflow.read(cfg))
        self.assertNotEqual(projects[0]['project']['source'],projects[1]['project']['source'])
        self.assertNotEqual(projects[0]['project']['model_namespace'],projects[1]['project']['model_namespace'])
        self.assertEqual(projects[0]['request']['firstperson'],projects[1]['request']['firstperson'])
        self.assertEqual(projects[0]['request']['firstperson']['sleeves'],'from_user_character')
        self.assertEqual(projects[0]['checkpoints'],['physics'])
        for cfg in projects:
            self.assertIsNone(cfg['request']['outfit'])
            self.assertEqual(cfg['request']['wardrobe']['mode'],'reserve')
            self.assertEqual(cfg['request']['expressions']['mode'],'reserve')
            self.assertFalse(cfg['request']['expressions']['audio_lip_sync'])

    def test_project_cannot_overwrite_source_or_existing_workspace(self):
        source=self.root/'source';source.mkdir()
        with self.assertRaises(ValueError):create_project.create('sample',source,source/'output')
        existing=self.root/'existing';existing.mkdir()
        with self.assertRaises(ValueError):create_project.create('sample',source,existing)

    def test_shared_hand_hashes_and_material_closure(self):
        asset=ROOT/'skill/assets/shared-hands';manifest=workflow.read(asset/'manifest.json')
        self.assertEqual(manifest['id'],'shared-firstperson-hands')
        self.assertFalse(manifest['full_character_mesh_included'])
        self.assertFalse(manifest['sleeves_included'])
        for rel,info in manifest['files'].items():
            p=asset/rel;self.assertEqual(workflow.digest(p),info['sha256'])
            self.assertEqual(p.stat().st_size,info['bytes'])
            if not rel.endswith(('.vmat_c','.vtex_c')):continue
            b=p.read_bytes();_,_,_,offset,count=struct.unpack_from('<IHHII',b)
            for i in range(count):
                entry=8+offset+12*i;tag,delta,n=struct.unpack_from('<4sII',b,entry)
                if tag!=b'RERL':continue
                start=entry+4+delta;relative,total=struct.unpack_from('<II',b,start)
                for j in range(total):
                    e=start+relative+16*j;pos=e+8+struct.unpack_from('<q',b,e+8)[0]
                    reference=b[pos:b.index(b'\0',pos)].decode()+'_c'
                    self.assertIn('runtime/'+reference,manifest['files'])

if __name__=='__main__':unittest.main()
