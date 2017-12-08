from tableausdk import *
from tableausdk.Extract import *
import numpy as np
import pandas as pd


# available tableau datatypes
# INTEGER, DOUBLE, BOOLEAN, DATE, DATETIME, DURATION, 
# CHAR_STRING, UNICODE_STRING, SPATIAL
mapper = {
    np.dtype(np.int64): {
        'tableau_datatype': Type.INTEGER,
        'tableau_set_function':Row.setInteger,
        'value_modifier': lambda x: [x] if not np.isnan(x) else None,
    },
    np.dtype(np.float64): {
        'tableau_datatype': Type.DOUBLE,
        'tableau_set_function':Row.setDouble,
        'value_modifier': lambda x: [x] if not np.isnan(x) else None,
    },
    np.dtype('O'): {
        'tableau_datatype': Type.UNICODE_STRING,
        'tableau_set_function':Row.setString,
        'value_modifier': lambda x: [unicode(x, errors='replace')] if x else None,
    },
    np.dtype('<M8[ns]'): {
        'tableau_datatype': Type.DATETIME,
        'tableau_set_function':Row.setDateTime,
        'value_modifier': lambda x: [x.year,x.month,x.day,x.hour,x.minute,x.second,0] if not np.isnan(x.year) else None,
    },
}

def tableau_datatype(dtype):
    return mapper[dtype]['tableau_datatype']

def make_table_definition(df):
    table_definition = TableDefinition()
    for column in df.columns:
        tableau_column = column.title().replace('_',' ')
        tableau_dtype = tableau_datatype(df[column].dtype)
        table_definition.addColumn(tableau_column,tableau_dtype)
    return table_definition

def dedup_column_name(df):
    # rename duplicate columns (https://stackoverflow.com/questions/24685012/pandas-dataframe-renaming-multiple-identically-named-columns)
    cols=pd.Series(df.columns)
    for dup in df.columns.get_duplicates(): cols[df.columns.get_loc(dup)]=[dup+'_'+str(d_idx) if d_idx!=0 else dup for d_idx in range(df.columns.get_loc(dup).sum())]
    df.columns=cols
    return df

def to_tde(df,tde_filename = 'extract.tde'):
    df = dedup_column_name(df)
    
    ExtractAPI.initialize()
    new_extract = Extract(tde_filename)
    
    table_definition = make_table_definition(df)
    new_table = new_extract.addTable('Extract', table_definition)
    
    for row in df.iterrows():
        new_row = Row(table_definition)
        for i,column in enumerate(df.columns):
            column_data_type = df[column].dtype
            value = mapper[column_data_type]['value_modifier'](row[1][i])
                
            if value:
                params = [new_row,i]+value
                mapper[column_data_type]['tableau_set_function'](*params)

        new_table.insert(new_row)
        
    new_extract.close()
    ExtractAPI.cleanup()

