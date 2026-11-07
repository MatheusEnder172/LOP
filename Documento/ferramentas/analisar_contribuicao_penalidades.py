import sys,time,numpy as np,pandas as pd
sys.path.insert(0,r"C:\us trem\Doc\UFMG\9\Lop\Codigo_v4\Código")
from scipy.optimize import minimize
from src.physics.pbm_batch import BatchPBMSolver
base=r"C:\us trem\Doc\UFMG\9\Lop\Codigo_v4"
met=pd.read_csv(base+r"\Código\outputs\etapa_2_1\tabela_metricas_otimizacao_inversa.csv")
ser=pd.read_csv(base+r"\Base de dados\raw\cinetica_batelada_A1_4.csv"); ser=ser[ser.t_min>0]
solver=BatchPBMSolver(); t=np.arange(1,61)*0.25
def termos(p,x,idx,lam=(1e-4,1e-4,1e-7,1e-6)):
    a1,b1,a2,b2,c=p; v=a1*np.exp(-b1*t)+a2*np.exp(-b2*t)+c
    r=solver.simulate_with_v_profile(t,-v); X=r['XZn']; d=r['delta']
    fit=float(np.sum((X[idx]-x)**2))
    return dict(fit=fit,cauda=lam[0]*v[-1]**2,delta=lam[1]*max(0,d[-1]-140)**2,a1=lam[2]*a1**2,b1=lam[3]*(b1-4)**2,v15=v[-1],d15=d[-1])
rows=[]
for _,m in met.iterrows():
    e=int(m.ensaio); s=ser[ser.ensaio==e].sort_values('t_min'); idx=[int(round(tt/0.25))-1 for tt in s.t_min]
    p=[m.a1,m.b1,m.a2,m.b2,m.c]; r=termos(p,s.XZn.values,idx); r['ensaio']=e; rows.append(r)
df=pd.DataFrame(rows).set_index('ensaio'); pd.set_option('display.width',200)
for c in ['cauda','delta','a1','b1']: df['razao_'+c]=df[c]/df['fit']
print(df.round(6).to_string())
print('\nmediana razões:',df[[c for c in df if c.startswith('razao')]].median().round(4).to_dict())
print('máx razões:',df[[c for c in df if c.startswith('razao')]].max().round(4).to_dict())
df.to_csv(r"C:\Users\USURIO~2\AppData\Local\Temp\claude\de529376d826b4eb\bccdb96a-f4b2-4f59-86ac-31b752ec7d68\scratchpad\contrib_penalidades.csv")
