import numpy as np
import pandas as pd
from scipy.stats import norm

def priip_rts1(df,rhp_range=np.arange(1,5),horizon=5,calcdate='20210331'):
    """
    df = DataFrame() with date and close
    rhp_range = range of rhps
    horizon = the sampling period in years
    calcdate = the calculation date
    """

    end_date = pd.to_datetime(calcdate)
    start_date = pd.to_datetime(calcdate)-pd.Timedelta(horizon*52,unit='W')
    idx = (df.index>=start_date)&(df.index<=end_date)
    df_rts = df.loc[idx,:].copy()
    df_ret = df_rts.pct_change().dropna(how='any')

    M0 = len(df_ret)
    M1 = np.mean(df_ret.values)
    M2 = np.sum((df_ret.values-M1)**2)/M0
    M3 = np.sum((df_ret.values-M1)**3)/M0
    M4 =  np.sum((df_ret.values-M1)**4)/M0

    mu = M1
    vol = np.sqrt(M2)
    skew = M3/(vol**3)
    kurt = M4/(vol**4)-3
    priip={}
    rhp_result = []
    mod_result  = []
    fav_result  = []
    unfav_result  = []
    stress_result  = []

    for rhp in rhp_range:
        print(rhp)
        N = rhp*256 #assuming 256 business days in a year
        stress_bucket =[63 if rhp>1 else 21][0]
        z = [99 if rhp<=1 else 90][0]
        za = [norm.ppf(0.01) if rhp<=1 else norm.ppf(0.05)][0]
        var =vol *np.sqrt(N)*(-1.96+0.474*skew/np.sqrt(N)-0.0687*kurt/N+0.146*(skew**2)/N)-0.5*N*(vol**2)
        VEV = (np.sqrt(3.842-2*var)-1.96)/np.sqrt(rhp)
        stressed_vol = np.percentile(df_ret.rolling(window=stress_bucket).apply(lambda x : np.std(x)).dropna(how='any').values,z)
        unfav = np.exp(M1*N+vol*np.sqrt(N)*(-1.28+0.107*skew/np.sqrt(N)+0.0724*kurt/N-0.0611*(skew**2)/N)-0.5*(vol**2)*N)
        fav = np.exp(M1*N+vol*np.sqrt(N)*(1.28+0.107*skew/np.sqrt(N)-0.0724*kurt/N+0.0611*(skew**2)/N)-0.5*(vol**2)*N)
        mod = np.exp(M1*N-vol*skew/6-0.5*(vol**2)*N)
        stress = za + ((za**2-1)/6)*skew/np.sqrt(N)+ ((za**3-3*za)/24)*kurt/N-((2*za**3-5*za)/36)*(skew**2)/N
        stress = np.exp(stressed_vol*np.sqrt(N)*stress-0.5*(stressed_vol**2)*N)
        rhp_result.append(rhp)
        fav_result.append(fav-1)
        mod_result.append(mod-1)
        unfav_result.append(unfav-1)
        stress_result.append(stress-1)

    return {'rhp':rhp_result,
            'mod':mod_result,
            'fav':fav_result,
            'stress':stress_result,
            'unfav':unfav_result
            }


def priip_rts2(df,rhp_range=np.arange(1,5),calcdate='20210331'):
    rhp_result = []
    mod_result  = []
    fav_result  = []
    unfav_result  = []
    stress_result  = []

    for rhp in rhp_range:
        horizon = np.max([10,rhp+5])

        start_date = pd.to_datetime(calcdate)-pd.Timedelta(int(horizon*52),unit='W')
        df_rts = df.loc[(df.index>=start_date)&(df.index<=calcdate),:].copy()
        sample_weeks=(df_rts.index[-1]-df_rts.index[0]).days/7
        if sample_weeks <int(horizon*52):
            pass

        # create Monthly observations
        dx = pd.DataFrame({'x':1},index=pd.bdate_range(start_date,calcdate,freq='BM'),)
        df_rts = pd.concat([dx,df_rts],axis=1)
        df_rts.dropna(how='any',inplace=True)
        df_rts = pd.concat([dx,df_rts['close']],axis=1)
        df_rts['close'].fillna(method='ffill',inplace=True)
        df_rts.drop('x',axis='columns',inplace=True)

        #create rolling overlapping window equal to RHP returns
        periods = rhp*12
        df_ret_7a = df_rts.copy()
        df_ret_7a['end_date']=df_ret_7a.index
        df_ret_7a['start_date']=df_ret_7a['end_date'].shift(periods=periods)
        df_ret_7a['ret']= df_ret_7a['close'].rolling(window=periods,min_periods=periods).apply(lambda x : x[-1]/x[0]-1)
        df_ret_7a['start_price']= df_ret_7a['close'].rolling(window=periods,min_periods=periods).apply(lambda x :x[0])
        df_ret_7a=df_ret_7a.rename(columns={'close':'end_price'})
        df_ret_7a.dropna(how='any',inplace=True)

        #create rolling overlapping window from 1 year to RHP
        min_month = 12
        max_month = rhp*12
        df_ret_7b= df_rts[-max_month-1:-min_month].copy()
        df_ret_7b['ret_raw']=0
        df_ret_7b['ret_raw']= df_rts['close'].values[-1]/df_ret_7b['close']-1
        df_ret_7b['end_price']=df_rts['close'].values[-1]
        df_ret_7b['end_date'] = df_rts.index[-1]
        df_ret_7b['start_date'] = df_ret_7b.index
        df_ret_7b['period'] = np.arange(max_month,min_month-1,-1)
        df_ret_7b['ret'] = np.power((df_ret_7b['ret_raw']+1),1/df_ret_7b['period'])
        df_ret_7b['ret'] = np.power(df_ret_7b['ret'],rhp)-1
        df_ret_7b=df_ret_7b.rename(columns={'close':'start_price'})

        #blending 7a and 7b together
        ret_7a_7b = np.append(df_ret_7b['ret'].values,df_ret_7a['ret'].values)

        mod = np.median(df_ret_7a['ret'].values)
        fav = np.max(df_ret_7a['ret'].values)
        unfav = np.min(ret_7a_7b)

        rhp_result.append(rhp)
        fav_result.append(fav)
        mod_result.append(mod)
        unfav_result.append(unfav)


        #calculation of the stress (same formula as the old RTS)
        end_date = pd.to_datetime(calcdate)
        start_date = pd.to_datetime(calcdate)-pd.Timedelta(horizon*52,unit='W')
        df_rts = df.loc[(df.index>=start_date)&(df.index<=end_date),:].copy()
        df_ret = df_rts.pct_change().dropna(how='any')
        M0 = len(df_ret)
        M1 = np.mean(df_ret.values)
        M2 = np.sum((df_ret.values-M1)**2)/M0
        M3 = np.sum((df_ret.values-M1)**3)/M0
        M4 =  np.sum((df_ret.values-M1)**4)/M0

        mu = M1
        vol = np.sqrt(M2)
        skew = M3/(vol**3)
        kurt = M4/(vol**4)-3

        N = rhp*256 #assuming 256 business days in a year
        stress_bucket =[63 if rhp>1 else 21][0]
        z = [99 if rhp<=1 else 90][0]
        za = [norm.ppf(0.01) if rhp<=1 else norm.ppf(0.05)][0]
        var =vol *np.sqrt(N)*(-1.96+0.474*skew/np.sqrt(N)-0.0687*kurt/N+0.146*(skew**2)/N)-0.5*N*(vol**2)
        stressed_vol = np.percentile(df_ret.rolling(window=stress_bucket).apply(lambda x : np.std(x)).dropna(how='any').values,z)

        stress = za + ((za**2-1)/6)*skew/np.sqrt(N)+ ((za**3-3*za)/24)*kurt/N-((2*za**3-5*za)/36)*(skew**2)/N
        stress = np.exp(stressed_vol*np.sqrt(N)*stress-0.5*(stressed_vol**2)*N)

        stress_result.append(stress-1)
    return {'rhp':rhp_result,
            'mod':mod_result,
            'fav':fav_result,
            'stress':stress_result,
            'unfav':unfav_result
            }



