import re

# define Python user-defined exceptions
class ParseError(Exception):
    """Base class for other exceptions"""
    def __init__(self,message:str):
        super().__init__(message)


class ODataQuery():
    '''
    Creates a query object out of a query_string 
    (e.g. "$select=one,two&$filter=one eq this and two eq that&$expand=object")
    '''

    def __init__(self,query_string:str):
        self.query_string = query_string
        self.result = {}
        self._filter_expr_dict = {}
        self.result = self.parse(self.query_string)

    def __getitem__(self, key):
        return self.result[key]

    def __setitem__(self,key,value):
        self.result[key]=value

    def keys(self):
        return self.result.keys()

    def values(self):
        return self.result.values()
        
    def parse(self,str:str):
        res_dict=self.__operator_dict(str)
        for key, value in res_dict.items():
            res_dict[key]=self.expression(operator=key,argument=value)
        return res_dict

    def expression(self,operator:str,argument:str):
        '''
        Parses the string for each operator
        '''
        if operator=='$select':
            return self.select(argument)
        if operator=='$filter':
            self._filter_expr_dict = {}
            return self.filter(argument)
        if operator=='$orderby':
            return self.orderby(argument)
        if operator=='$expand':
            return self.expand(argument)

    def select(self,str:str):
        return str.replace(' ','').split(',')

    def orderby(self,str:str):
        column = str.split(' ')[0]
        try:
            sort_method = str.split(' ')[1].lower()
        except KeyError:
            sort_method = 'asc'
        return {
            'column': column,
            'sort_method': sort_method
        }

    def filter(self,str:str):
        """
        Replace all sub-expressions with 'FLTR_EXPR'. 
        """
        expr_count = 0
        while True:
            sub_expression = re.findall(r'\(([\w\s\']+)\)',str)
            if sub_expression:
                expr_count += 1
                result=self.filter(sub_expression[0])
                self._filter_expr_dict[f'FLTR_EXPR_{expr_count}']=result
                str=str.replace(f'({sub_expression[0]})',f'FLTR_EXPR_{expr_count}')
            else:
                break
        # no parenthesis are left, parse expression
        return self.__parse_expression(str)
    
    def expand(self,str):
        object = str.split('(')[0]
        try:
            query = self.parse(str.split('(')[1][:-1])
        except IndexError:
            query =None
        return {
            'object':object,
            'query':query
        }


    def __operator_dict(self,str):
        '''
        Parses the query string and retruns a dictionary in the form:
        {
            '$select':'one,two',
            '$filter':'one eq this and two eq that'
            ...
        }
        '''
        result=re.split(r'([\&\$]+[\w]+)=(?![^(]*\))',str)
        result = [elem for elem in result if elem!=''] #remove empty 
        result = list(map(lambda x: x[1:] if x[0]=='&' else x,result)) #remove leading &
        result = dict(zip(result[0::2],result[1::2]))
        for key, value in result.items():
            assert key[0]=='$' #Check if key is a command
            assert value[0]!='$' #Check if value is not a command
        return result

    def __parse_expression(self,expr:str):
        '''
        Parses the expression (expr). If the expression contains ' and ' or ' or ', then it calls itself recursively again.
        '''
        if (' and ' in expr) or (' or ' in expr):
            return self.__parse_and_or(expr)

        if expr.strip()[0:10]=='FLTR_EXPR_':
            return self._filter_expr_dict[expr.strip()]
        else:
            expr = [elem for elem in re.split(r'^(.+) ((?:eq|or|lt|gt)) (.+)$',expr) if elem != '']
            return {
                    'left': expr[0].replace('"',''),
                    'operator':expr[1],
                    'right': expr[2].replace('"','')
            }

    def __parse_and_or(self,str:str):
        res = {}
        contains_and = ' and ' in str
        contains_or = ' or ' in str
        if contains_and and contains_or:
            raise ParseError("Filter statement contains both and and or. Parser can handle only one of them at the same time")
        
        if contains_and:
            res['and']=[]
            for elem in str.split(' and '):
                res['and'].append(self.__parse_expression(elem))
        elif contains_or:
            res['or']=[]
            for elem in str.split(' or '):
                res['or'].append(self.__parse_expression(elem))
        return res

        
