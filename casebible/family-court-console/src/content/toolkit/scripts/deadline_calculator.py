#!/usr/bin/env python3
"""Candidate deadline arithmetic only; no appellate deadlines."""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
from _common import banner, write_json
LIMITS=['This is arithmetic, not legal advice. CONFIRM WITH THE CLERK.','Refuses appellate deadlines and treats court holidays/closures as unverified unless supplied.','Service add-ons and local practices require verification against current rule/order.']
def parse(s): return dt.date.fromisoformat(s)
def business_adjust(d, holidays):
 while d.weekday()>=5 or d.isoformat() in holidays: d+=dt.timedelta(days=1)
 return d
def candidate(trigger, days, holidays, label):
 # Rule-style conservative calculation: day after trigger is day 1 for calendar interval.
 raw=trigger+dt.timedelta(days=days)
 due=business_adjust(raw,holidays)
 return {'label':label,'trigger_date':trigger.isoformat(),'raw_candidate':raw.isoformat(),'candidate_due_date':due.isoformat(),'holiday_or_closure_unverified':not bool(holidays),'warning':'CONFIRM WITH THE CLERK; hearing notice, service method, court order, and current rule can change this date.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--trigger-date',required=True);p.add_argument('--kind',required=True,choices=['referee-objection','motion-before-hearing','response-before-hearing','local-objection-service','local-objection-certificate','service-addon']);p.add_argument('--service-method',default='unknown');p.add_argument('--holidays-json');p.add_argument('--output');p.add_argument('--dry-run',action='store_true');a=p.parse_args();print(banner('deadline_calculator.py',LIMITS))
 holiday=set(json.loads(Path(a.holidays_json).read_text())) if a.holidays_json else set(); t=parse(a.trigger_date)
 mapping={'referee-objection':(21,'Candidate MCR 3.215 objection window'),'motion-before-hearing':(-7,'Candidate local motion timing (count backward from hearing)'),'response-before-hearing':(-3,'Candidate local response timing (count backward from hearing)'),'local-objection-service':(-9,'Candidate local packet service timing (confirm current packet)'),'local-objection-certificate':(-7,'Candidate local packet certificate timing (confirm current packet)'),'service-addon':(3,'Candidate service-method add-on (confirm MCR 2.107(C))')}
 days,label=mapping[a.kind]; raw=t+dt.timedelta(days=days); due=business_adjust(raw,holiday)
 result={'tool':'deadline_calculator.py','limitations':LIMITS,'kind':a.kind,'service_method':a.service_method,'dry_run':a.dry_run,'result':{'label':label,'trigger_date':t.isoformat(),'raw_candidate':raw.isoformat(),'candidate_date':due.isoformat(),'holiday_or_closure_unverified':not bool(holiday),'warning':'CONFIRM WITH THE CLERK. Not valid as the sole basis for a filing date; no appellate calculations.'}}
 write_json(a.output,result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
