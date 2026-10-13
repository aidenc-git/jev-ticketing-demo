import json
from dataclasses import replace
from unittest.mock import patch
import pytest
from app.models import Ticket, TriageResult
from app.router import apply_routing
from app.jev_triage import MockTriager
from app.store import TicketStore
from app.service import TicketService


def triage(**changes):
    return replace(TriageResult('billing', .9, 1.0, .9, .05, .05, 'test'), **changes)

@pytest.mark.parametrize('category,queue', [('billing','Billing Team'),('technical','Engineering Support'),('account','Account Services'),('feature_request','Product Team'),('other','General Support')])
def test_routing_categories(category,queue):
    t=apply_routing(Ticket('title','description','test@example.com'),triage(category=category))
    assert t.assigned_queue==queue

@pytest.mark.parametrize('score,label,hours', [(0,'Low',72),(1,'Medium',24),(2,'High',8),(3,'Critical',1)])
def test_priority_sla(score,label,hours):
    t=apply_routing(Ticket('t','d','test@example.com'),triage(priority_score=score))
    assert (t.priority_label,t.sla_hours)==(label,hours)

def test_escalation_floor():
    t=apply_routing(Ticket('t','d','test@example.com'),triage(priority_score=0,escalate_probability=.7))
    assert t.escalated and t.priority_label=='High' and t.sla_hours==8

def test_manual_review():
    t=apply_routing(Ticket('t','d','test@example.com'),triage(category_confidence=.59))
    assert t.needs_review and t.assigned_queue=='Manual Review'

def test_mock_triage():
    result=MockTriager().triage('Refund requested','Please refund this invoice')
    assert result.category=='billing' and result.refund_probability>.7

def test_storage_round_trip(tmp_path):
    path=tmp_path/'tickets.json'
    store=TicketStore(path)
    t=apply_routing(Ticket('test','desc','test@example.com'),triage())
    store.add(t)
    saved=TicketStore(path).get(t.id.lower())
    assert saved and saved.triage.category=='billing'

def test_service_lifecycle(tmp_path):
    with patch('app.service.TicketStore',side_effect=lambda:TicketStore(tmp_path/'tickets.json')), patch('app.service.get_triager',return_value=MockTriager()):
        service=TicketService()
        try:
            t=service.create_ticket('Login issue','I forgot my password','test@example.com')
            assert service.get_ticket(t.id).id==t.id
            assert t.assigned_queue=='Account Services'
            assert service.update_status(t.id,'resolved').status=='resolved'
            with pytest.raises(ValueError): service.update_status(t.id,'invalid')
            assert len(service.list_tickets())==1
        finally: service.close()

def test_fallback_on_api_error(tmp_path):
    class BrokenTriager:
        name='broken'
        def triage(self,*args): raise RuntimeError('network failure')
        def close(self): pass
    with patch('app.service.TicketStore',side_effect=lambda:TicketStore(tmp_path/'tickets.json')),patch('app.service.get_triager',return_value=BrokenTriager()):
        service=TicketService()
        try:
            t=service.create_ticket('Invoice issue','Please refund this charge','test@example.com')
            assert t.triage.model=='mock-keyword-v1'
        finally: service.close()
