import base64
import io
import sys
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine

def fixture():
    return """EPISODE NUMBER: Episode 1
--- SCRIPT START ---
SCENE 01
Scene heading: INT. OFFICE - NIGHT
Scene start: 00:00.000
Scene end: 01:00.000
**MARA (Angry):** Start: (00:00.000) | End: (00:03.000)
"You stole my company. Give it back."
**CAMERA:** Start: (00:00.000) | End: (01:00.000)
A clear view of the office.
**VICTOR (Cold):** Start: (00:05.000) | End: (00:09.000)
"You signed the transfer."
**MARA (Urgent):** Start: (00:12.000) | End: (00:16.000)
"That signature is not mine."
**VICTOR (Threatening):** Start: (00:20.000) | End: (00:24.000)
"Show the evidence and I will arrest your brother."
**MARA (Shaken):** Start: (00:28.000) | End: (00:32.000)
"What did you make him sign?"
**VICTOR (Threatening):** Start: (00:40.000) | End: (00:44.000)
"Unless you leave, I will call security."
--- SCRIPT END ---"""

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.eps=engine.parse_files([("episode.txt",fixture().encode())])
        self.candidates,_=engine.retrieve(self.eps)
    def test_centiseconds(self): self.assertEqual(engine.ms("01:02.34"),62340)
    def test_milliseconds(self): self.assertEqual(engine.ms("01:02.345"),62345)
    def test_tenths(self): self.assertEqual(engine.ms("00:01.2"),1200)
    def test_format_roundtrip(self): self.assertEqual(engine.ms(engine.tc(123456)),123456)
    def test_parse(self): self.assertEqual(len(self.eps[0]["events"]),7)
    def test_no_header_leak(self): self.assertNotIn("EPISODE",self.eps[0]["events"][0]["text"])
    def test_dialogue_overlap(self):
        self.assertFalse(engine.safe(4000,[{"kind":"DIALOGUE","start_ms":2100,"end_ms":4200},{"kind":"DIALOGUE","start_ms":3600,"end_ms":8200}]))
    def test_exact_boundary(self): self.assertTrue(engine.safe(3000,self.eps[0]["events"]))
    def test_candidates(self): self.assertGreater(len(self.candidates),0)
    def test_lengths(self): self.assertTrue(all(20000<=c["duration_ms"]<=60000 for c in self.candidates))
    def test_all_valid(self): self.assertTrue(all(engine.validate(c,{1:self.eps[0]})["passed"] for c in self.candidates))
    def test_mid_dialogue_invalid(self):
        c={**self.candidates[0],"segments":[engine.segment(self.eps[0],1000,32000)],"duration_ms":31000}
        self.assertIn("DIALOGUE_CUT",engine.validate(c,{1:self.eps[0]})["violations"])
    def test_duration_sum(self):
        self.assertIn("DURATION",engine.validate({**self.candidates[0],"duration_ms":20001},{1:self.eps[0]})["violations"])
    def test_missing_delimiter(self):
        with self.assertRaises(ValueError):engine.parse_files([("a.txt",b"broken")])
    def test_duplicate_episode(self):
        with self.assertRaises(ValueError):engine.parse_files([("a.txt",fixture().encode()),("b.txt",fixture().encode())])
    def test_scene_warning_preserves(self):
        raw=fixture().replace("Scene end: 01:00.000","Scene end: 00:45.000")
        ep=engine.parse_files([("a.txt",raw.encode())])[0]
        self.assertTrue(ep["events"][1]["parse_warnings"])
        self.assertEqual(ep["events"][1]["end_ms"],60000)
    def test_invalid_interval_rejected(self):
        raw=fixture().replace("End: (00:03.000)","End: (00:00.000)")
        with self.assertRaises(ValueError):engine.parse_files([("a.txt",raw.encode())])
    def test_unsafe_zip(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:z.writestr("../evil.txt","x")
        with self.assertRaises(ValueError):engine.unpack([{"name":"a.zip","data":base64.b64encode(b.getvalue()).decode()}])
    def test_zip_read_without_extract(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w") as z:z.writestr("folder/a.txt",fixture())
        self.assertEqual(len(engine.unpack([{"name":"a.zip","data":base64.b64encode(b.getvalue()).decode()}])),1)
    def test_unknown_extension(self):
        with self.assertRaises(ValueError):engine.unpack([{"name":"a.exe","data":"eA=="}])
    def test_no_inputs(self):
        with self.assertRaises(ValueError):engine.unpack([])
    def test_no_model_pass_by_rules(self):self.assertFalse(any(c.get("semantic_gate_passed") for c in self.candidates))
    def test_generic_sound_no_hook(self):
        ev=[dict(kind="SOUND FX",start_ms=0,end_ms=2000,text="Carriage door slamming shut.",event_id="x")]
        self.assertEqual(engine.features(ev,0,22000)[0]["hook"],0)
    def test_impact_dedup(self):
        ev=[dict(kind="ACTION",start_ms=0,end_ms=1000,text="She punches the guard.",event_id="x"),dict(kind="SOUND FX",start_ms=200,end_ms=1000,text="A punch lands.",event_id="y")]
        self.assertEqual(engine.features(ev,0,22000)[0]["hook"],2)
    def test_unknown_review_id(self):
        with self.assertRaises(ValueError):engine.apply_reviews(self.candidates,[{"promo_id":"invented"}],"ranker")
    def test_model_score_out_of_bounds(self):
        with self.assertRaises(ValueError):engine.apply_reviews(self.candidates,[dict(promo_id=self.candidates[0]["promo_id"],hook=5)],"ranker")
    def test_unseen_names_not_hardcoded(self):
        ep=engine.parse_files([("a.txt",fixture().replace("MARA","TESS").encode())])
        self.assertTrue(any(r["raw_label"]=="TESS" for r in engine.registry(ep)))
    def test_overlapping_repeated_footage(self):
        c=dict(segments=[engine.segment(self.eps[0],0,24000),engine.segment(self.eps[0],20000,44000)],duration_ms=48000)
        self.assertIn("REPEATED_FOOTAGE",engine.validate(c,{1:self.eps[0]})["violations"])
    def test_partial_visual_evidence_is_retained(self):
        c=self.candidates[0]
        camera=next(e for e in c["events"] if e["kind"]=="CAMERA")
        cliff=c["cliffhanger_event_ids"]
        r=dict(promo_id=c["promo_id"],hook=3,coherence=3,cliffhanger=3,trope_fit=3,stitch_legibility=4,hook_event_ids=[camera["event_id"]],cliffhanger_event_ids=cliff,open_question="Will she expose the forgery?",rationale="Fixture",audience_tags=["broad_cold"],risk_codes=[],stitch_justification=None,verdict="pass")
        engine.apply_reviews([c],[r],"ranker")
        self.assertNotIn("HOOK_EVIDENCE_INVALID",c["risk_codes"])
    def test_missing_review_bounded_repair(self):
        batch=[{"promo_id":"A"},{"promo_id":"B"}]
        with patch.object(engine,"compact",side_effect=lambda c:c),patch.object(engine,"model_call",side_effect=[[{"promo_id":"A"}],[{"promo_id":"B"}]])as call:
            result=engine.review_batch(batch,"fixture","groq","ranker",[])
            self.assertEqual([r["promo_id"]for r in result],["A","B"])
            self.assertEqual(call.call_count,2)
    def test_unknown_model_id_rejected_before_repair(self):
        with patch.object(engine,"compact",side_effect=lambda c:c),patch.object(engine,"model_call",return_value=[{"promo_id":"BAD"}]):
            with self.assertRaises(ValueError):engine.review_batch([{"promo_id":"A"}],"fixture","groq","ranker",[])
    def test_compact_preserves_dialogue_and_action(self):
        c=self.candidates[0]
        compact=engine.compact(c)
        original={e["event_id"]for e in c["events"]if e["kind"]!="CAMERA"}
        retained={e["event_id"]for e in compact["events"]if e["kind"]!="CAMERA"}
        self.assertEqual(original,retained)
    def test_no_evidence_means_no_gate_pass(self):
        c=self.candidates[0]
        r=dict(promo_id=c["promo_id"],hook=4,coherence=4,cliffhanger=4,trope_fit=4,stitch_legibility=4,hook_event_ids=[],cliffhanger_event_ids=[],verdict="pass")
        engine.apply_reviews([c],[r],"critic")
        self.assertFalse(c["semantic_gate_passed"])
    def valid_review(self,c):
        return dict(promo_id=c["promo_id"],hook=4,coherence=4,cliffhanger=4,trope_fit=4,stitch_legibility=4,hook_event_ids=c["hook_event_ids"],cliffhanger_event_ids=c["cliffhanger_event_ids"],open_question="Will she expose the forgery?",stitch_justification="Same scene, chronological omission.",verdict="pass")
    def test_missing_question_fails_gate(self):
        c=self.candidates[0];r=self.valid_review(c);r["open_question"]=""
        engine.apply_reviews([c],[r],"ranker")
        self.assertFalse(c["semantic_gate_passed"])
        self.assertIn("OPEN_QUESTION_MISSING",c["risk_codes"])
    def test_low_stitch_fails_composite_gate(self):
        c=self.candidates[0];c["format"]="composite";r=self.valid_review(c);r["stitch_legibility"]=1
        engine.apply_reviews([c],[r],"ranker")
        self.assertFalse(c["semantic_gate_passed"])
        self.assertIn("STITCH_GATE_FAILED",c["risk_codes"])
    def test_missing_stitch_justification_fails_gate(self):
        c=self.candidates[0];c["format"]="composite";r=self.valid_review(c);r["stitch_justification"]=None
        engine.apply_reviews([c],[r],"ranker")
        self.assertFalse(c["semantic_gate_passed"])

if __name__=="__main__":unittest.main()
