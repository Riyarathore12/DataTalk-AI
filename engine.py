import pandas as pd, numpy as np, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def records(df):
    return __import__('json').loads(df.to_json(orient='records',date_format='iso'))
def overview(df):
    return dict(rows=len(df),columns=len(df.columns),missing=int(df.isna().sum().sum()),duplicates=int(df.duplicated().sum()),fields=[dict(name=str(c),type=str(df[c].dtype),missing=int(df[c].isna().sum())) for c in df],preview=records(df.head(8)),stats=records(df.select_dtypes('number').describe().T.reset_index()) if len(df.select_dtypes('number').columns) else [])
INTENTS={'mean':'average mean typical','sum':'total sum combined','max':'maximum highest largest max','min':'minimum lowest smallest min','count':'count number how many rows records','missing':'missing null empty values','duplicates':'duplicate repeated rows','group':'by per grouped breakdown category','correlation':'correlation relationship association','distribution':'distribution histogram spread'}
def ask(df,q):
    q=q.lower().strip(); names=list(df.columns); numeric=list(df.select_dtypes('number').columns)
    matched=[c for c in names if re.search(r'(?<!\w)'+re.escape(str(c).lower())+r'(?!\w)',q)]
    v=TfidfVectorizer().fit_transform([q]+list(INTENTS.values())); scores=cosine_similarity(v[0],v[1:])[0]; intent=list(INTENTS)[int(scores.argmax())]
    if not scores.max(): raise ValueError('Try average, total, highest, lowest, count, missing, duplicates, correlation or distribution, with column names.')
    if re.search(r'\b(where|filter|between|after|before|excluding|except|greater|less|only|top|bottom|most|least)\b',q): raise ValueError('Conditional and ranked queries are not supported yet. Use an aggregate or grouped query.')
    nums=[c for c in matched if c in numeric]; cats=[c for c in matched if c not in numeric]
    if intent=='missing': return dict(answer=f'{int(df.isna().sum().sum())} missing cells.',table=[{'column':str(c),'missing':int(df[c].isna().sum())} for c in names])
    if intent=='duplicates': return dict(answer=f'{int(df.duplicated().sum())} duplicate rows.')
    if intent=='correlation':
        if len(nums)!=2: raise ValueError('Name exactly two numeric columns for correlation.')
        val=df[nums[0]].corr(df[nums[1]]); return dict(answer=f'Pearson correlation: {val:.4f}' if pd.notna(val) else 'Correlation is undefined for these values.')
    grouped=bool(re.search(r'\b(by|per|grouped|breakdown)\b',q))
    if grouped:
        if len(cats)!=1 or len(nums)!=1: raise ValueError('Name one numeric and one categorical column, e.g. total Sales by Region.')
        agg=next((a for a in ['sum','mean','max','min','count'] if any(re.search(r'\b'+w+r'\b',q) for w in INTENTS[a].split())),None)
        if not agg: raise ValueError('Specify total, average, maximum, minimum or count.')
        s=df.groupby(cats[0],dropna=False)[nums[0]].agg(agg).sort_values(ascending=False); t=s.head(30).reset_index(); return dict(answer=f'{agg.title()} of {nums[0]} by {cats[0]} (up to 30 groups).',table=records(t),chart=records(t))
    if intent=='count' and not matched: return dict(answer=f'{len(df):,} rows in the dataset.')
    if len(nums)!=1: raise ValueError('Specify exactly one numeric column.')
    c=nums[0]; s=df[c].dropna()
    if intent=='distribution':
        if s.empty: raise ValueError('No numeric values.')
        counts,edges=np.histogram(s,bins=10); t=[{'range':f'{edges[i]:.2f}–{edges[i+1]:.2f}','count':int(n)} for i,n in enumerate(counts)]; return dict(answer=f'Distribution of {c} (10 bins).',table=t,chart=t)
    if intent not in ['sum','mean','max','min','count']: raise ValueError('Please specify an aggregation.')
    val=getattr(s,intent)(); return dict(answer=f'{intent.title()} of {c}: {val:,.4g}' if pd.notna(val) else 'No valid values.')

def clean(df,method):
    df=df.drop_duplicates().copy()
    if method=='drop': return df.dropna()
    if method=='fill':
        for c in df:
            s=df[c]; val=s.median() if pd.api.types.is_numeric_dtype(s) else (s.mode().iloc[0] if not s.mode().empty else 'Unknown'); df[c]=s.fillna(val)
    return df
