import pytest 

@pytest.fixture
def ODataQuery():
    from bootstrapi.parser import ODataQuery
    res=ODataQuery
    return res

def test_select(ODataQuery):
    result = ODataQuery(("$select=one,two&$expand=other_object($select=first,second&$filter=one eq 'this' and two eq 'that')&$filter=(one eq 'this' and two eq 'that') or (two gt 2 and (one lt 3 and two gt 3))&$orderby=one asc"))
    assert result['$select'] == ['one', 'two']

def test_expand(ODataQuery):
    result = ODataQuery(("$select=one,two&$expand=other_object($select=first,second&$filter=one eq 'this' and two eq 'that')&$filter=(one eq 'this' and two eq 'that') or (two gt 2 and (one lt 3 and two gt 3))&$orderby=one asc"))
    assert result['$expand'] == {
        'object': 'other_object', 
        'query': {
            '$select': ['first', 'second'], 
            '$filter': {
                'and': [
                    {'left': 'one', 'operator': 'eq', 'right': "'this'"}, 
                    {'left': 'two', 'operator': 'eq', 'right': "'that'"}
                    ]}}}

def test_expand_simple(ODataQuery):
    result = ODataQuery(("$expand=other_object"))
    assert result['$expand']['object']=='other_object'

def test_filter(ODataQuery):
    result = ODataQuery(("$select=one,two&$expand=other_object($select=first,second&$filter=one eq 'this' and two eq 'that')&$filter=(one eq 'this' and two eq 'that') or (two gt 2 and (one lt 3 and two gt 3))&$orderby=one asc"))
    assert result['$filter'] == {
        'or': [
            {'and': [
                {'left': 'one', 'operator': 'eq', 'right': "'this'"}, 
                {'left': 'two', 'operator': 'eq', 'right': "'that'"}]}, 
            {'and': [
                {'left': 'two', 'operator': 'gt', 'right': '2'}, 
                {'and': [
                    {'left': 'one', 'operator': 'lt', 'right': '3'}, 
                    {'left': 'two', 'operator': 'gt', 'right': '3'}]}]}]}
    result = ODataQuery("$filter=one eq 'this'")
    assert result['$filter']=={'left': 'one', 'operator': 'eq', 'right': "'this'"}

def test_filter_no_brackets(ODataQuery):
    assert ODataQuery("$filter=name eq 'datahub' or name eq 'salesforce'")['$filter']=={'or': [{'left': 'name', 'operator': 'eq', 'right': "'datahub'"}, {'left': 'name', 'operator': 'eq', 'right': "'salesforce'"}]}


def test_filter_spaces(ODataQuery):
    assert ODataQuery("$filter=name eq \"create datamodel\"")


def test_orderby(ODataQuery):
    result = ODataQuery(("$select=one,two&$expand=other_object($select=first,second&$filter=one eq 'this' and two eq 'that')&$filter=(one eq 'this' and two eq 'that') or (two gt 2 and (one lt 3 and two gt 3))&$orderby=one asc"))
    assert result['$orderby']== {'column': 'one', 'sort_method': 'asc'}

